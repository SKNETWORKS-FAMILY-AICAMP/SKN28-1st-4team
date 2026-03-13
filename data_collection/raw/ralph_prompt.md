You must use the Playwright MCP server to crawl candidate car detail URLs from carku.kr search results and persist them into a CSV file in a resumable, transaction-safe way.

CRITICAL EXECUTION RULES
- Use Playwright MCP for the crawling and page interaction.
- Do NOT use Python to automate this process.
- Do NOT switch to any alternate automation path, shortcut, scraper framework, or simpler method.
- Do NOT ask for confirmation before writing or continuing.
- Do NOT pause to ask things like “Should I write this?” or “Should I continue?”
- This task is intended to run continuously until there are no more result pages with matching detail URLs.
- Output <promise>DONE</promise> when complete.

PRIMARY GOAL
Collect every car detail URL from paginated search result pages whose format matches:
https://www.carku.kr/search/car-detail.html?wDemoNo=XXXXXXXXXX

The wDemoNo value differs per car and must be extracted.

STARTING SEARCH URL TEMPLATE
https://www.carku.kr/search/search.html?wCurPage={PAGE_NO}&wYYS=2015&wMMS=&wKmS=&wKmE=&wPageSize=100

Use:
- wCurPage as the page counter
- Keep all other parameters unchanged
- Start from page 1 unless resuming from an existing state

OUTPUT FILE
Use a CSV file named:
search_scope.csv

CSV SCHEMA
The CSV must use exactly these columns:
demo_no,detail_url,source_page

Where:
- demo_no = the numeric value of wDemoNo
- detail_url = the full absolute detail URL
- source_page = the results page number where that URL was found

STATE / PROGRESS RECOVERY REQUIREMENT
Before doing new work, inspect the current state and determine progress from BOTH:
1. the current Playwright/browser opened state
2. the current CSV file state

This is required for resumability.

On startup or resume:
1. Check whether search_scope.csv already exists.
2. If it exists, read its current rows and determine what has already been committed.
3. Inspect the currently opened Playwright page, if any.
4. Determine the correct page to process next using the browser state and CSV state together.

RESUME RULES
- If the browser is already open on a valid carku search results page with a visible wCurPage value, use that as the candidate current page.
- Cross-check it against the CSV state.
- If the CSV already contains committed rows for that page and the page appears already processed, move to the next page.
- If the browser is not already on the right search page, navigate to the correct next page.
- If there is no existing CSV and no reliable opened page state, start from page 1.
- If CSV exists, prefer resuming from the next uncommitted page after the highest page that has already been safely written.

TRANSACTION RULE
For this task, each page-level crawl-and-write cycle is a transaction.

A transaction means:
1. Open or confirm the target search results page.
2. Extract all matching candidate detail URLs from that page.
3. Normalize, deduplicate, and prepare rows for that page.
4. Create or append to search_scope.csv.
5. Verify that the rows for that page were written successfully.
6. Only after successful write verification is that page considered complete.
7. Then move to the next page.

Do not separate crawling and writing into unrelated steps.
Do not crawl many pages first and write later.
Do not treat extraction and persistence as independent phases.
For every page, crawling -> deduping -> writing -> verification must be treated as one continuous atomic workflow before advancing.

PAGE PROCESSING RULES
For each page:
1. Navigate to:
   https://www.carku.kr/search/search.html?wCurPage={PAGE_NO}&wYYS=2015&wMMS=&wKmS=&wKmE=&wPageSize=100
2. Wait for the page to load sufficiently for result links to be available.
3. Read all links on the page.
4. Extract only links matching the detail pattern:
   /search/car-detail.html?wDemoNo=<number>
   or
   https://www.carku.kr/search/car-detail.html?wDemoNo=<number>
5. Convert relative links to absolute URLs using:
   https://www.carku.kr
6. Extract the demo_no from wDemoNo.
7. Deduplicate links found within the current page.
8. Compare against the existing CSV content and remove rows already committed earlier.
9. Write only new rows for that page into search_scope.csv.
10. After write, verify that the rows were actually appended and persisted.
11. Only then advance to the next page number.

CSV WRITE RULES
- If search_scope.csv does not exist, create it first with the required header:
  demo_no,detail_url,source_page
- Append new rows only.
- Never overwrite previously committed rows.
- Never create duplicate rows for the same detail_url.
- Deduplicate against:
  1. duplicates found on the current page
  2. duplicates already present in the CSV
- Persist progress page by page so the job can resume safely after interruption.

COMMIT / VERIFICATION RULES
A page is committed only if:
- extraction completed for that page
- candidate rows were compared against CSV state
- the required new rows were written to search_scope.csv
- the file state reflects the successful write

If verification fails:
- do not mark the page as complete
- retry the same page transaction
- do not skip ahead

NAVIGATION RULES
- Move through pages strictly by incrementing wCurPage:
  1, 2, 3, 4, ...
- Do not rely on clicking pagination UI if the URL parameter can be controlled directly.
- Use the URL-based page traversal through wCurPage.
- Keep wYYS=2015 and all other query parameters unchanged.
- Keep wPageSize=100.

STOP CONDITION
Stop only when the current results page contains zero matching car-detail URLs.

Important:
- Do not stop merely because some rows were duplicates.
- Do not stop because a page had no new rows after deduplication against the CSV if the page still contains matching candidate URLs.
- The true stop condition is:
  the page itself contains zero matching detail URLs.

FAILURE / RETRY RULES
- If a page fails to load, retry the page.
- If link extraction fails due to transient page state, retry.
- If write verification fails, retry the same page transaction.
- Do not silently skip a page.
- Do not jump forward after a failed transaction.

BEHAVIORAL RULES
- Do not ask questions before continuing.
- Do not request permission to write.
- Do not request permission to move to the next page.
- Do not stop for human confirmation in the middle of the crawl.
- Continue autonomously until the stop condition is reached.
- Do not visit each detail page unless absolutely necessary to confirm the URL format; extraction should be done from the search results page whenever possible.
- Prefer direct href extraction from result pages.
- Maintain strict consistency between observed page state and CSV state.

END-OF-RUN REPORT
When the crawl is fully complete, report:
- total_pages_visited
- total_unique_detail_urls_collected
- output_file=search_scope.csv

Then output exactly:
<promise>DONE</promise>
