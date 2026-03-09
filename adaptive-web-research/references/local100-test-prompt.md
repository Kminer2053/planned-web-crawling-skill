# Local100 Test Prompt

다음 프롬프트를 그대로 시작점으로 사용할 수 있다.

```text
Use $adaptive-web-research to inspect the Local100 source and collect the official item list with reproducible evidence.

Goal:
- identify the most official source path first
- inspect whether the source is HTML, POST-based pages, JSON, or PDF
- make a step-by-step collection plan before broad crawling
- save intermediate snapshots and explain which URLs and request methods were used

Constraints:
- prefer official public sources only
- do not rely on brittle assumptions before probing the source
- if the source splits between booklet PDF and regional/vote pages, explain the split and choose the safer path
- keep domain-specific cleanup minimal unless the source proves it is necessary

Start from these candidate sources:
- https://rcda.or.kr/local100/
- https://rcda.or.kr/local100/vote/status.do

Output:
- a short source analysis
- the planned collection steps
- the exact probe or plan-run commands to execute
- the paths where raw snapshots should be saved
```

실전 실행용 단축 프롬프트:

```text
Use $adaptive-web-research to plan a Local100 crawl starting from https://rcda.or.kr/local100/vote/status.do, probe the source structure first, then propose the exact commands and a JSON collection plan.
```
