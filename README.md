# GenAI Internship

Work record of my Generative AI internship. It shows what I built and what I learned while working with large language models.

## What I worked on

I started with basic model calls and moved to prompt design for daily use cases. I wrote short scripts that take a clear input and return a clean result. Each script fixed a small task end to end.

## Navigate the days

Day folders use two-digit numbers from Day01 onward, so the GitHub file browser keeps them in order.

| Day | Folder | Work |
| --- | --- | --- |
| Day 1 | [Day01](./Day01) | Mistral quickstart, tokens and transformers notes |
| Day 2 | [Day02](./Day02) | Sentiment prompts and tokenization notes |
| Day 3 | [Day03](./Day03) | Hinglish and Gujlish dare generator |
| Day 4 | [Day04](./Day04) | Task1 support reply, Task2 product description |
| Day 5 | [Day05](./Day05) | Task3 email classifier, Task4 meeting actions |
| Day 6 | [Day06](./Day06) | Task5 social post, Task6 code explainer |
| Day 7 | [Day07](./Day07) | Task7 translator, Task8 cover letter |
| Day 8 | [Day08](./Day08) | Task9 moderation, Task10 interview questions |
| Day 9 | [Day09](./Day09) | Task11 review sentiment, Task12 quiz generator |
| Day 10 | [Day10](./Day10) | JSON review parser |
| Day 11 | [Day11](./Day11) | Streaming demo and flashcard generator |
| Day 12 | [Day12](./Day12) | Customer support dashboard, resume screener, AI content studio |
| Day 13 | [Day13](./Day13) | ChromaDB and Milvus vector store RAG demos with library policy documents |
| Day 14 | [Day14](./Day14) | Chat with PDF: pypdf text extraction, ChromaDB retrieval, Mistral grounded answers |
| Day 15 | [Day15](./Day15) | Company knowledge assistant and customer support doc bot: RAG with citations, fallback, and chat memory |
| Day 16 | [Day16](./Day16) | Chat with PDF: pypdf extraction, ChromaDB index for multiple files, Mistral answers with sources |
| Day 17 | [Day17](./Day17) | Tool calling bot: no-argument timetable tool, Mistral tool loop, answers grounded in the tool result |
| Day 18 | [Day18](./Day18) | Chat memory app: session-state history, last 10 messages, two argument-taking timetable tools |
| Day 19 | [Day19](./Day19) | Cafe menu tool-calling bot and Streamlit Tavily stationery bot |
| Day 20 | [Day20](./Day20) | Cafe AI agent with a think, act, observe tool loop |
| Day 21 | [Day21](./Day21) | Single AI agent (LinkedIn post) and sequential multi-agent (product review) |
| Day 22 | [Day22](./Day22) | Production safety notes: memory, guardrails, prompt injection, LLM evaluation |
| Day 23 | [Day23](./Day23) | General knowledge answer evaluator: Mistral answers, Groq scores the answer (Streamlit) |
| Day 24 | [Day24](./Day24) | Cinema support agent: router sends each question to a booking or snacks specialist |
| Day 25 | [Day25](./Day25) | Hotel concierge: router sends each question to room service, reservations, or general |
| Day 26 | [Day26](./Day26) | Bank account specialist: router label plus a tool loop, card confirmation, and PII masking |
| Day 27 | [Day27](./Day27) | Streamlit support dashboard: chat memory, routed labels, tool calls, model dropdown |
| Day 28 | [Day28](./Day28) | Hotel Guest Assistant core hub: router, moderation, room service, reservations, facilities, FAQ |
| Day 29 | [Day29](./Day29) | Hotel Guest Assistant knowledge build: handbook RAG, web search, concierge, marketing, sentiment, summary, quiz |
| Day 30 | [Day30](./Day30) | Hotel Guest Assistant final build: bill loop, masking, confirmation, Groq judge, CV screener, dashboard, handoff, unit tests |

Every day folder runs on its own. Put a `.env` file inside the folder with the keys that day needs (`MISTRAL_API_KEY`, plus `GROQ_API_KEY` for Day23, and `TAVILY_API_KEY` for Day29 when the fallback is used) before running a script. The `.env` files stay out of git.

## Skills I used

* Prompt design with role and output shape stated in plain words.
* Review of outputs across tones and levels so replies fit the case.
* Careful test runs with sample inputs before marking a task done.

## Outcome

This repo holds my full task set from the internship period.
