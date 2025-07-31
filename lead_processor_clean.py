# This is a temporary file to create the clean lead processor
# The old social scraping methods need to be removed from lines 372-801

# Remove these methods:
# - _extract_instagram_meta_data (line 372)
# - _scrape_facebook (line 431)
# - _scrape_facebook_apify (line 445)
# - _scrape_facebook_fallback (line 496)
# - _scrape_linkedin (line 552)
# - _extract_email_from_text (line 669)
# - _extract_phone_from_text (line 686)
# - _extract_recent_posts (line 714)

# These should be removed because they're redundant - SocialMediaScraper handles all this now