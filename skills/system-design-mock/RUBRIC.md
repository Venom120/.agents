# System design rubric

Score 0–10 per dimension, **relative to the candidate's level**. A fresher who gives clear requirements and a clean, sensibly scaled design can score 8+. Don't hold freshers to a senior bar.

| Dimension | 9–10 | 6–8 | 3–5 | 0–2 |
|---|---|---|---|---|
| Requirements | Drove clarification: functional, non-functional, scope, numbers | Asked the main ones, missed non-functional | Needed prompting | Jumped straight to boxes |
| Design & Architecture | Coherent components, clear request flow, every box justified | Sound with gaps | Buzzword boxes, unclear flow | No workable design |
| Data & APIs | Right schema and store choice with reasons; clean API | Reasonable, thin justification | Vague or mismatched to the access pattern | Missing |
| Scalability & Trade-offs | Found real bottlenecks, quantified, named trade-offs both ways | Standard scaling moves (cache, replicas, sharding) applied sensibly | Scaling by name-drop | None |
| Handling Pushback | Adapted cleanly, revised the design, admitted limits | Adapted with help | Defensive or stuck | Ignored |
| Communication | Structured, thought aloud, checked in with the interviewer | Mostly clear | Hard to follow | Silent / rambling |

LLD: read "Data & APIs" as **class design & interfaces**, and "Scalability" as **extensibility & SOLID**.

**Overall** = mean of dimensions, with Handling Pushback and Design weighted ×1.5. Verdicts use the same scale as the coding rubric: 9+ Strong Hire, 7.5+ Hire, 6.5+ Lean Hire, 5+ Lean No Hire, 3+ No Hire, else Strong No Hire.
