from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uuid

from app.config import CORS_ORIGINS, MAX_UPLOAD_MB, SUPABASE_STORAGE_BUCKET
from app.db import get_supabase
from app.schemas import TenderCreate, BidCreate, DecisionRequest, ComplianceEvaluateRequest, ExtractRequest, AuditCreate
from app.services.extraction import extract_fields, extract_text_from_file
from app.services.verification import verify_document, cross_document_checks
from app.services.compliance import evaluate_compliance
from app.services.audit import record_audit

app = FastAPI(title="Innovexia Bid Compliance Backend", version="1.0.0",
              description="Prototype API for tender, bid, document, verification, compliance, decision, and audit workflows.")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
                   allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

def _one(table, row_id):
    r=get_supabase().table(table).select("*").eq("id",row_id).limit(1).execute()
    return r.data[0] if r.data else None

@app.get("/")
def root():
    return RedirectResponse(url="/site/index.html")

@app.get("/health")
def health():
    try:
        get_supabase().table("bids").select("id").limit(1).execute()
        return {"status":"ok","database":"connected"}
    except Exception as e:
        raise HTTPException(503,detail=f"Database connection failed: {str(e)}")

@app.get("/tenders")
def list_tenders(status: str | None = None):
    q=get_supabase().table("tenders").select("*").order("created_at",desc=True)
    if status: q=q.eq("status",status)
    return q.execute().data

@app.post("/tenders")
def create_tender(body: TenderCreate):
    row={"tender_number":body.tender_number,"title":body.title,"description":body.description,
         "requirements":body.requirements,"status":body.status,"created_by":body.created_by}
    try:
        data=get_supabase().table("tenders").insert(row).execute().data
        record_audit("TENDER_CREATED",details={"tender_number":body.tender_number})
        return data[0] if data else row
    except Exception as e: raise HTTPException(400,detail=str(e))

@app.get("/tenders/{tender_id}")
def get_tender(tender_id: str):
    row=_one("tenders",tender_id)
    if not row: raise HTTPException(404,"Tender not found")
    return row

@app.post("/bids")
def create_bid(body: BidCreate):
    row=body.model_dump(exclude_none=True)
    try:
        data=get_supabase().table("bids").insert(row).execute().data
        bid=data[0] if data else row
        record_audit("BID_SUBMITTED",bid_id=bid.get("id"),actor_id=body.bidder_id,actor_role="bidder")
        return bid
    except Exception as e: raise HTTPException(400,detail=str(e))

@app.get("/bids/{bid_id}")
def get_bid(bid_id: str):
    row=_one("bids",bid_id)
    if not row: raise HTTPException(404,"Bid not found")
    return row

@app.get("/bids/{bid_id}/documents")
def list_documents(bid_id: str):
    return get_supabase().table("bidder_documents").select("*").eq("bid_id",bid_id).order("created_at",desc=True).execute().data

@app.post("/bids/{bid_id}/documents")
async def upload_document(bid_id: str, document_type: str = Query(...), file: UploadFile = File(...)):
    kind=document_type.upper()
    if kind not in ("PAN","GST","UDYAM"):
        raise HTTPException(400,"document_type must be PAN, GST, or UDYAM")
    content=await file.read()
    if len(content)>MAX_UPLOAD_MB*1024*1024:
        raise HTTPException(413,f"File exceeds {MAX_UPLOAD_MB} MB limit")
    ext=Path(file.filename or "upload.bin").suffix.lower()
    object_path=f"{bid_id}/{kind.lower()}/{uuid.uuid4().hex}{ext}"
    try:
        get_supabase().storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            object_path,content,{"content-type":file.content_type or "application/octet-stream","upsert":"false"})
        row={"bid_id":bid_id,"document_type":kind,"file_name":file.filename,
             "storage_path":object_path,"mime_type":file.content_type,"upload_status":"UPLOADED"}
        saved=get_supabase().table("bidder_documents").insert(row).execute().data
        record_audit("DOCUMENT_UPLOADED",bid_id=bid_id,details={"document_type":kind,"file_name":file.filename})
        return saved[0] if saved else row
    except Exception as e: raise HTTPException(400,detail=f"Upload failed: {str(e)}")

@app.post("/extract/{document_type}")
def extract_document(document_type: str, body: ExtractRequest):
    kind=document_type.upper()
    if kind != body.document_type:
        raise HTTPException(400,"Path and body document_type must match")
    fields=extract_fields(kind,body.ocr_text)
    return {"document_type":kind,"document_id":body.document_id,"fields":fields,
            "extraction_status":"EXTRACTED" if any(fields.values()) else "REVIEW",
            "note":"Extraction does not prove authenticity."}

@app.post("/crosscheck/{document_type}")
async def crosscheck(document_type: str, bidder_id: str, file: UploadFile = File(...)):
    kind=document_type.upper()
    if kind not in ("PAN","GST","UDYAM"):
        raise HTTPException(400,"document_type must be PAN, GST, or UDYAM")
    content=await file.read()
    if len(content)>MAX_UPLOAD_MB*1024*1024: raise HTTPException(413,"File too large")
    text,source=extract_text_from_file(file.filename or "",content)
    fields=extract_fields(kind,text)
    if not any(fields.values()):
        return {"document_type":kind,"overall":"unreadable","checks":[
            {"label":"document text","status":"unreadable","extracted":None,"registered":None}],
            "message":"No readable text was extracted. Connect the OCR engine or submit a text-based PDF/TXT for this prototype."}
    try:
        result=verify_document(kind,bidder_id,fields)
        result["extraction"]=fields
        result["source"]=source
        return result
    except Exception as e: raise HTTPException(400,detail=str(e))

@app.post("/verify/{bid_id}")
def verify_bid(bid_id: str):
    bid=_one("bids",bid_id)
    if not bid: raise HTTPException(404,"Bid not found")
    bidder=_one("bidders",bid.get("bidder_id"))
    if not bidder: raise HTTPException(404,"Bidder not found")
    output={"bid_id":bid_id,"bidder_id":bid.get("id"),"documents":{}}
    for kind,field in (("PAN","pan_number"),("GST","gst_number"),("UDYAM","udyam_number")):
        value=bidder.get(field)
        if not value:
            output["documents"][kind]={"overall":"review","message":f"{field} is missing from bidder record"}
            continue
        # Use stored OCR record when available; compare against reference.
        cfg={"PAN":("pan_verifications_ocr","pan_number"),"GST":("gst_verifications_ocr","gstin"),"UDYAM":("udyam_verifications_ocr","udyam_number")}[kind]
        try:
            rows=get_supabase().table(cfg[0]).select("*").eq(cfg[1],value).limit(1).execute().data
            ocr=rows[0] if rows else {cfg[1]:value,"organization_name":bidder.get("organisation_name")}
            output["documents"][kind]=verify_document(kind,bidder["id"],ocr,bid_id)
        except Exception as e:
            output["documents"][kind]={"overall":"review","message":str(e)}
    try:
        pan_rows=get_supabase().table("pan_verifications_ocr").select("*").eq("pan_number",bidder.get("pan_number")).limit(1).execute().data
        gst_rows=get_supabase().table("gst_verifications_ocr").select("*").eq("gstin",bidder.get("gst_number")).limit(1).execute().data
        udyam_rows=get_supabase().table("udyam_verifications_ocr").select("*").eq("udyam_number",bidder.get("udyam_number")).limit(1).execute().data
        output["cross_document"]=cross_document_checks(pan_rows[0] if pan_rows else None,gst_rows[0] if gst_rows else None,udyam_rows[0] if udyam_rows else None)
    except Exception as e: output["cross_document"]={"overall":"review","message":str(e),"checks":[]}
    statuses=[x.get("overall") for x in output["documents"].values()]
    output["overall"]="VERIFIED" if statuses and all(x=="match" for x in statuses) and output["cross_document"].get("overall")=="match" else "REVIEW"
    record_audit("BID_VERIFICATION_COMPLETED",bid_id=bid_id,details={"overall":output["overall"]})
    return output

@app.post("/compliance/evaluate")
def compliance_evaluate(body: ComplianceEvaluateRequest):
    bid=_one("bids",body.bid_id)
    if not bid: raise HTTPException(404,"Bid not found")
    requirements=body.rules or bid.get("tender_requirements") or {}
    rows=get_supabase().table("bidder_verification_data").select("*").eq("bid_id",body.bid_id).limit(1).execute().data
    if not rows: raise HTTPException(404,"No bidder_verification_data row found for this bid")
    result=evaluate_compliance(requirements,rows[0])
    record_audit("COMPLIANCE_EVALUATED",bid_id=body.bid_id,details={"overall":result["overall"],"score":result["score"]})
    return result

@app.post("/bids/{bid_id}/decision")
def submit_decision(bid_id: str, body: DecisionRequest):
    bid=_one("bids",bid_id)
    if not bid: raise HTTPException(404,"Bid not found")
    update={"status":body.decision,"decision_remarks":body.remarks,
            "decision_by":body.officer_id,"decision_at":datetime.now(timezone.utc).isoformat()}
    try:
        saved=get_supabase().table("bids").update(update).eq("id",bid_id).execute().data
        record_audit("OFFICER_DECISION",bid_id=bid_id,actor_id=body.officer_id,actor_role="procurement_officer",details=update)
        try:
            get_supabase().table("notifications").insert({"bid_id":bid_id,"recipient_id":bid.get("bidder_id"),
                "title":"Bid decision updated","message":f"Your bid status is {body.decision}.","is_read":False}).execute()
        except Exception:
            pass
        return saved[0] if saved else update
    except Exception as e: raise HTTPException(400,detail=str(e))

@app.get("/bids/{bid_id}/audit")
def get_bid_audit(bid_id: str):
    return get_supabase().table("audit_logs").select("*").eq("bid_id",bid_id).order("created_at",desc=True).execute().data

@app.get("/notifications")
def list_notifications(recipient_id: str):
    return get_supabase().table("notifications").select("*").eq("recipient_id",recipient_id).order("created_at",desc=True).execute().data

@app.post("/audit")
def create_audit(body: AuditCreate):
    try: return record_audit(body.action,body.bid_id,body.actor_id,body.actor_role,body.details)
    except Exception as e: raise HTTPException(400,detail=str(e))


# Serve the bundled static frontend from the same origin as the API.
app.mount("/site", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "frontend"), html=True), name="site")
