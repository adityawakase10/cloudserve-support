# Discovery notes: interviews

## Marcus Adeyemi (Head of Support)
- **What he told me:**
    - takes north of 500 tickets a week and has 6 agents.
    - service agreement says first response within 2 hours but they are averaging somewhere     between 8 and 12 hours
    - Tried canned  response library which took more time instead of reducing it.
    - Wants the chatbot to answer the easy tickets so his agents can handle the hard ones.
    - Mentioned that he doesn't care how the chatbot works but wants the first response time number to come down because he can't add more agents to his team.
    - Mentioned that First contact resolution (FCR) matters the most to him.
    - Mentioned their ticket resolution rate is at 42% whereas the industry bechmark that people quote to him is 65%
    - Mentioned that if the chatbot sends wrong answer, that would make this project a failure. He prefers the chatbot answer nothing than it said something wrong.
    - Second failure for the project would be if the chatbot increases the work for his agents rather than reducing it like it happened with the canned response library.
    - The tickets they receive are usually about Authentication, deployment problems, billing questions, API questions.
    - Does not know the breakdown of the tickets they receive.
    - Mentioned that Enterprise customers have a different agreement and they will notice  immediately if they get worse service than they were getting.
    - Has a compliance review coming up in Autumn. So whatever they do has to be explainable.
- **What he seems not to know:**
    - Does not know the breakdown of the tickets they receive.
    - Will get to know other missing info once going to other interviews
- **What I want to check in the data:**
    - average response time
    - validate the ticket resolution rate. He mentioned 42%
    - The types of tickets they receive. He mentioned - Authentication, deployment problems, billing questions, API questions.
    - exact breakdown of the tickets.
    - Do enterprise customers get better or worse outcomes than others?

## Sofia Restrepo (Tier 1 agent)
- **What she told me:**
    - gets around 40 to 70 tickets. Most tickets on Mondays.
    - takes 4-5mins to resolve known tickets. If anything unusual, takes around 40mins to analyze and the escalates the ticket.
    - Could resolve most of the tickets (7 out of 10) without looking anything up. Frequest tickets are about - Password lockouts, rate limits, why is my invoice higher, my deployment keeps rolling back. she sorts the queue by age (oldest first), not by urgency
    - times is wasted in finding the answers and writing them down from the documentation. Hence they have made their own files of answers from which they copy.Each agent keeps a personal file of past answers and copies from it.
    - Mentioned that Daniel has his own copy of answers too which is better than hers.
    - Mentioned to Ines that the search is the problem. But due to miscommunication, Ines thought the documentation is bad.
    - Three reasons for escalation:
        a) Do not know the answer
        b) Not confident enough about the answer because if it is wrong then it will come back worse
        c) If the ticket is about a security problem as they have been asked to escalate it regardless.
    - Doesn't want to system to send wrong answers to customers because she will have to answer to the angry customers for the answers she did not give. Instead wants the system to hands her a ticket with a draft and the relevant page attached.
    - Mentioned that language is an issue when the customer's first language isn't english. They usually have the worst satisfaction scores.
- **What he seems not to know:**
    - she trusts her personal answer file
- **What I want to check in the data:**
    - can resolve 7-in-10 tickets
    - why tickets get escalated
    - types of tickets she receive
    - low satisfaction scores from customers not good with english
## Daniel Okonkwo (Tier 2 engineer)
- **What he told me:**
    - About half of what reaches tier 2 could have been solved by tier 1 if they had been confident or found the right page. Many he closes by pasting a link and two sentences.
    - Escalations arrive as the raw forwarded ticket: no summary, no note of what was tried. He re-reads everything and often re-asks the customer something they were already asked. He says this frustrates customers more than the waiting.
    - Wants context with every escalation: what the ticket is about, the relevant docs, and what the system was unsure about. "I do not need it to be right. I need it to show its working." Would be twice as fast.
    - Warning: personal answer files contain answers that were correct two years ago and are wrong now. Learning from current answers would scale up mistakes.
    - Must never be automated: security / account compromise, billing disputes (no commitments about money), data location (compliance risk).
- **What he seems not to know:**
    - She thinks tier 1 escalates solvable tickets because they lack confidence or can't find the page. Sofia confirms both, but adds a third reason he doesn't mention: If the ticket is about a security problem as they have been asked to escalate it regardless.
- **What I want to check in the data:**
    - Of escalated tickets, what share were answerable from the docs? (He says about half.)
    - How common are the "never automate" types: security, billing disputes, data location?


## Ines Varga (Technical writer)
- **What she told me:**
    - 29 support articles (separate from product docs), reviewed on a rotation. Covers authentication, deployment, API, billing, data, security, account.
    - Customers use them a lot; the support team doesn't use them at all. She saw replies that were her articles rewritten from memory.
    - Cause: internal search only matches titles and exact words. Customers describe problems differently ("my deployment keeps dying" vs her title "resolving container health check failures").
    - Her 29 articles are accurate; the agents' private answer files have never been reviewed. She has asked twice for them to be consolidated.
    - Would be comfortable with a system answering from her articles, but wants every answer to show which article it came from, so she can tell if the article is wrong or the system misread it.
    - Not covered by any article: feature requests, roadmap / timing questions, brand-new incidents (rare, but a wrong answer there does the most damage).
- **What she seems not to know:**
    - She knows agents don't use her articles, but not know what they use instead, which is their own perosnal documents with answers and Daniel says those contain outdated answers which are now wrong.
- **What I want to check in the data:**
    - What share of tickets are answerable from the documentation?
    - Which ticket types have no article at all (feature requests, roadmap)?

## Ravi Menon (Customer, business plan)
- **What he told me:**
    - Support is slow but good once you reach a person. A ticket raised in the afternoon gets a reply the next day.
    - How much the wait hurts depends on urgency: a "how does pagination work" question can wait; a deployment failing at 9am makes a 4-hour wait serious. "Same queue, completely different cost to me."
    - While waiting he searches the docs himself and finds the answer about half the time. The reply that arrives later usually says the same thing.
    - Fine with an automated first reply if it is honest: what it thinks, the page it came from, and that a person will confirm. Will not accept something confident and wrong.
    - Wants to be told when a reply is automated, so he knows how much to trust it.
    - An enterprise colleague gets answers in about an hour. If the gap between plans grows, it will come up at renewal.
- **What he seems not to know:**
    - He assumes urgent tickets should be answered first, but Sofia says the queue is actually sorted by age (oldest first), not by urgency
- **What I want to check in the data:**
    - Do high-urgency tickets get resolved faster than low-urgency ones?
    - Do enterprise customers really get faster answers than business customers?

## Patterns I'm seeing
- Answers exist but can't be found quickly: Marcus (canned library), Sofia (doc search is painful), Ines (search only matches exact titles).
- they all want the system to show its source and admit when it’s unsure. Transparency matters more to them than perfect accuracy. That directly shapes the design (citations, confidence, escalation with context),