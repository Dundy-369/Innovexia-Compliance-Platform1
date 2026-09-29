# Pramaan prototype — updated flow

Key changes:
- index.html: procurement-focused hero visual and scroll-reveal feature animations.
- login.html: Buyer, Bidder and Procurement Officer roles; OTP/Digital Signature login options and guest access removed.
- register.html: Buyer and Bidder retained; dedicated Procurement Officer registration with requested identity, organization, role and verification documents.
- create-tender.html: bidder-query, auto-extension and reverse-auction controls removed.
- buyer-dashboard.html and bidder-dashboard.html: Support sidebar entry removed.
- procurement-officer-dashboard.html: new officer command center linking to the existing tender, bidder, compliance, analytics, notification and settings pages.
- assets/procurement-hero.svg: local hero illustration, so the landing page does not depend on an external image host.

Prototype routing:
Login -> Buyer dashboard / Bidder dashboard / Procurement Officer dashboard
Register -> Buyer dashboard / Bidder dashboard / Procurement Officer dashboard
Officer dashboard -> all major procurement workflow pages.


Final navigation update: sticky Pramaan Assistant is present on every HTML page, including index.html. Support navigation has been removed from all three dashboards.
