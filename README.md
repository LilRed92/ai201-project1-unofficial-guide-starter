# The Unofficial Guide — Project 1

A retrieval-augmented generation (RAG) system that answers questions about the
fan-built lore, setlist patterns, and pit etiquette of **Sleep Token**, **Ghost**,
and **Rob Zombie**, grounded entirely in collected Reddit threads.

---

## Domain

My system covers the unofficial, community-built knowledge around three theatrical
heavy bands — Sleep Token, Ghost, and Rob Zombie — spanning two kinds of knowledge:
the deep narrative *lore* (who Papa Emeritus is, what the deity "Sleep" represents,
how the Vessel storyline unfolds across albums) and the practical *concert culture*
(mosh-pit etiquette, hearing protection, phone use, crowd safety). This knowledge
is valuable precisely because it lives nowhere official: band websites sell tickets
and merch but never explain that all Papas share one green and one white eye, or
that the polite way to be near the stage without moshing is to hug the perimeter of
the circle pit. That information is scattered across enormous Reddit mega-threads
and only makes sense once someone has read dozens of comments — which is exactly
what a RAG system is good at compressing.

---

## Document Sources

Ten plain-text files (`doc1.txt`–`doc10.txt`), each scraped from ten separate Reddit threads,
together covering lore and concert culture for all three bands.

| # | Source (subreddit) | Type | File / URL |
|---|--------|------|-----------------|
| 1 | r/SleepToken | Reddit thread | `documents/doc1.txt` — track-by-track breakdown of Vessel's relationship with the deity Sleep · https://www.reddit.com/r/SleepToken/comments/13tsicb/the_complete_lore_of_sleep_token/ |
| 2 | r/SleepToken | Reddit thread | `documents/doc2.txt` — debate over whether Sleep is a literal deity, Hypnos, or a toxic relationship · https://www.reddit.com/r/SleepToken/comments/1gyfnd8/the_lore/ |
| 3 | r/SleepToken | Reddit thread | `documents/doc3.txt` — first-concert survival guide (crowd weight, etiquette, merch lines) · https://www.reddit.com/r/SleepToken/comments/1jj00jg/first_concert_what_to_expect/ |
| 4 | r/SleepToken | Reddit thread | `documents/doc4.txt` — what to expect at a show (phones, hydration, post-concert emotions) · https://www.reddit.com/r/SleepToken/comments/1ecqvny/going_to_see_sleep_token_on_nov_very_excited_what/ |
| 5 | r/GhostBand | Reddit thread | `documents/doc5.txt` — the Clergy, the Ministry, and the chronological ascension of the Papas · https://www.reddit.com/r/GhostBand/comments/1f7e2ln/can_someone_explain_the_lore_of_ghost/ |
| 6 | r/Ghostbc | Reddit thread | `documents/doc6.txt` — full timeline of how the mic passes between Papa Emeritus incarnations · https://www.reddit.com/r/Ghostbc/comments/9lx0bc/full_ghost_lore/ |
| 7 | r/GhostBand | Reddit thread | `documents/doc7.txt` — overview of the Nameless Ghouls and the quasi-religious hierarchy · https://www.reddit.com/r/GhostBand/comments/16a9jvq/can_someone_please_explain_ghost_lore/ |
| 8 | r/Explainlikeimscared | Reddit thread | `documents/doc8.txt` — heavy-metal GA survival, earplugs, navigating the pit perimeter · https://www.reddit.com/r/Explainlikeimscared/comments/1s2c4im/what_should_i_expect_from_a_heavy_metal_concert/ |
| 9 | r/AftershockFestival | Reddit thread | `documents/doc9.txt` — unwritten rules of crowd surfing, slam dancing, and pit safety · https://www.reddit.com/r/AftershockFestival/comments/1nxojzd/psa_for_mosh_pits_just_crowds/ |
| 10 | r/StLouis | Reddit thread | `documents/doc10.txt` — crowd energy and pit behavior specific to a Rob Zombie show · https://www.reddit.com/r/StLouis/comments/1f78rbx/rob_zombie_show/ |

These threads are the right source because the questions that most would care about ("what do all
the Papas have in common?", "how do I avoid the pit?") are answered only as
community consensus emerging across many comments, never as a single authoritative
document.

---

## Chunking Strategy

**Chunk size:** 900 characters · **Overlap:** 175 characters · **Method:**
paragraph-aware packing (implemented in `chunk_documents.py`).

After cleaning each thread (stripping titles, `Author:`/`Subreddit:` labels,
per-comment author headers, markdown, HTML, and non-English comments), each
surviving Reddit comment becomes one unit. The chunker greedily
packs consecutive whole paragraphs into a chunk until adding the next would exceed
900 characters, then repeats the trailing paragraph(s) that fit within 175
characters at the start of the next chunk for overlap. A single paragraph longer
than 900 characters is the only case that falls back to a word-boundary split, so
chunks never cut mid-word and almost never mid-comment. This produced **219 chunks**
across the 10 documents, with lengths varying (~350–900 chars) because they follow
real comment boundaries.

900 characters fits these documents because a single lore explanation or a piece of
concert advice is usually one medium Reddit comment — small enough to embed cleanly
in `all-MiniLM-L6-v2`'s ~256-token window without truncation, but large enough to
keep a full thought (e.g. "all Papas share one green and one white eye") together
rather than splitting a theory across chunks. **If the documents were much longer**
(wiki articles instead of comments) I would raise the chunk size and switch to a
recursive/section-aware splitter; **if they were much shorter** (one-line reviews)
I would drop overlap to near zero and pack many more units per chunk, since the
risk of splitting a thought disappears.

---

## Sample Chunks

```
Chunk 1 — Source: doc1.txt | Index: 12
─────────────────────────────────────────────────────
VI. THIS PLACE WILL BECOME YOUR TOMB "Atlantic" - (Vessel) Vessel wakes up in a hospital after a failed suicide attempt, perhaps to sever his connection with Sleep, and is talked through the damage. He begs to not be woken up and slowly falls back into Sleep's grasp throughout the course of this album. "Hypnosis" - (Vessel - Sleep) Vessel implores Sleep to once again lift him out, and offers himself to them despite knowing how much it affected him. "The Offering" was the same but he did not know, this song is sadder because he is helpless even after knowing and offers himself up to Sleep the exact same way. "Mine" - (Vessel - Sleep) Vessel believes the relationship is destined to be and that no matter how much he tries to distance himself with Sleep, they'll surely cross paths again. He lies to himself more to make himself feel okay instead of facing the truth.
```

```
Chunk 2 — Source: doc5.txt | Index: 4
─────────────────────────────────────────────────────
Each Papa (minus Nihil) stays for one album and and handful of tours per cycle. At the end of their tours, they are then retired in some way. All of the Papas are from the Emeritus bloodline. They all have a familial trait: their eyes. One eye is green, and the other is white. Papa Emeritus I (his name is Primo) was the first introduced when the band started. His album was Opus Eponymous, and he headed the first tours. Due to him being the first Papa, his personality wasn't too heavily fleshed out like the others. At the end of his tour, he simply retired, and his younger brother ascended to Papa.
```

```
Chunk 3 — Source: doc6.txt | Index: 11
─────────────────────────────────────────────────────
4. The eye. At first it was thought that one white eye has been genetically passed through the bloodline, it's what originally sparked the theory that Papas were related. However during Dance Macabre we see that during Nihil's initiation, Sister punched him in the eye (that's how you get anisocoria IRL also.) which gave him the one white eye. So I guess we can conclude that it's part of the initiation and not genetics. HOWEVER... Cardinal Copia. He has the white eye despite not being Papa, and he's also not part of the bloodline (officially). So, if even the cardinals have the white eye then it's done to everyone who joins the clergy. Also, Papa 1 originally had two white eyes in the short Ritual promo video, but Tobias said he had to stop wearing the other contact due to his eye rejecting it. - Unanswered Questions 1.
```

```
Chunk 4 — Source: doc8.txt | Index: 7
─────────────────────────────────────────────────────
2. General etiquette is to keep moshing limited to a circle, often with bigger guys standing at the perimeter to act as a shield for folks who don't want to participate. It should be easy to steer clear of if you don't want to be a part of it. If someone's being violent, moshing around people who don't want it, etc. other folks or security do often step in.
```

```
Chunk 5 — Source: doc10.txt | Index: 8
─────────────────────────────────────────────────────
He did say "Never gonna stop me, never gonna stop!" He runs from one spot to another to another. It's always been strangely choreographed. I've been to over a thousand concerts and RZ put on one of the best shows across all genres. I'd be out of breath if I was wild'n out on stage like he does too. Aww man, we have to have standards. Watch any video of Mick Jagger. He bounces all over, is already old, and hits his notes. I've been to four Rob Zombie shows. I've lost count of how many different bands across different genres in so many different kinds of venues.... If you think that's the best show you've ever seen, I'm sorry, or we have very different ideas as to what a great show entails. I agree completely. Who cares really about his lyrics when he's putting on a show with so much to look at? Who cares about the music he's playing?
```

---

## Embedding Model

- **Model:** `all-MiniLM-L6-v2`
- **Initialization (in `retrieval.py`):** `SentenceTransformer("all-MiniLM-L6-v2")`
- **Runs:** fully locally via `sentence-transformers` — no API key, no rate limits.

`all-MiniLM-L6-v2` is a good fit for a prototype like this: it is small (~22M
parameters), runs on CPU in well under a second per query, and embeds my whole
219-chunk corpus in a couple of seconds, so iterating on chunking and retrieval was
fast and free. The main tradeoff I accepted is **embedding quality vs. model size /
domain fit**: the model has never seen Sleep Token / Ghost jargon, so casually
phrased fan text ("phone down hands up") doesn't always land close to a formally
phrased query ("cell phone usage at rituals") — the exact gap that caused my Q5
failure below. For a production deployment where **cost wasn't a constraint** I would
move to an API-hosted, higher-dimensional model (e.g. Voyage or OpenAI embeddings),
accepting added **latency and per-call cost** in exchange for stronger handling of
domain-specific vocabulary and paraphrase, and would consider light **domain
fine-tuning** on the band-lore corpus so queries and passages share an embedding
space even when their wording differs.

---

## Retrieval Test Results

(Distances are cosine distance from the live ChromaDB collection; lower = closer.)

```
Query: "According to the community lore, what specific physical trait is shared by all Papas from the Emeritus bloodline?"

Top Results:
  Rank 1 | Distance: 0.3776 | Source: doc5.txt
  Each Papa (minus Nihil) stays for one album and and handful of tours per cycle. At the end of their tours, they are then retired in some way. All of the Papas are from the Emeritus bloodline. They all have a familial trait: their eyes. One eye is green, and the other is white. Papa Emeritus I (his name is Primo) was the first introduced when the band started. His album was Opus Eponymous, and he headed the first tours. Due to him being the first Papa, his personality wasn't too heavily fleshed out like the others. At the end of his tour, he simply retired, and his younger brother ascended to Papa.

  Rank 2 | Distance: 0.4745 | Source: doc6.txt
  4. The eye. At first it was thought that one white eye has been genetically passed through the bloodline, it's what originally sparked the theory that Papas were related. However during Dance Macabre we see that during Nihil's initiation, Sister punched him in the eye (that's how you get anisocoria IRL also.) which gave him the one white eye. So I guess we can conclude that it's part of the initiation and not genetics. HOWEVER... Cardinal Copia. He has the white eye despite not being Papa, and he's also not part of the bloodline (officially). So, if even the cardinals have the white eye then it's done to everyone who joins the clergy. Also, Papa 1 originally had two white eyes in the short Ritual promo video, but Tobias said he had to stop wearing the other contact due to his eye rejecting it. - Unanswered Questions 1.

  Rank 3 | Distance: 0.4792 | Source: doc6.txt
  Cardi B is confirmed as the new leader. She lead the world to stupidity now she leads them to Lucifer as Mama Emeritus I don't think she's his son, but I do want to know what Copia's origin/lineage is I would love to know who the mother for all the Papas are since we know Papa Nihil is their father, but he and Sister Imperator clearly have had a little something something going on Good job . Maybe we can keep this going by having us Ghost old times add additional stories of their favorite Ghost experiences of the past, what ever that might be. I want to point out that in the Papaganda videos, the 'hard rocking sexy beat' and 'refined wine' lines are Papa II's ego while talking about himself.

  Rank 4 | Distance: 0.4893 | Source: doc7.txt
  Papa Emeritus: The character of Papa Emeritus serves as the lead singer and spiritual leader of the band. There have been several iterations of Papa Emeritus, each with a different number (e.g., Papa Emeritus I, II, III, IV, etc.). This change represents the passing of the torch to a new character over time. The Nameless Ghouls: The instrumental members of the band are called the "Nameless Ghouls." They are typically dressed in matching, anonymous costumes, often resembling clergy or monks. Storyline: Ghost's lore weaves a complex narrative, involving themes of the occult, Satanism, and a quasi-religious hierarchy. The band's music and lyrics often revolve around these themes.

  Rank 5 | Distance: 0.4954 | Source: doc6.txt
  Sadly for him, it was not enough. - September 30th, 2017 In the middle of performing Monstrance Clock, men in suits got on stage and took away Papa Emeritus 3. Right after that, an old man, followed by two more men in suits, carrying an oxygen mask for him got to the center of the stage. He introduced himself as Papa Emeritus Zero and informed us that the party was over and that it was time for the dark ages. - March, 2018 Back in the Ministry, Papa Emeritus Zero is talking to Sister Imperator. She informs him that its time for new blood as his sons didn't manage to complete the mission. They needed someone like Zero but in his youth. We learn now that all three previous Papas were his sons. Somebody knocks on the door, and that is Cardinal Copia. Papa Zero was not very happy about that at first but he agreed to take him under his wing and guide him on his way.
```

**Relevance explanation:** The top result (doc5.txt, 0.3776) is the correct chunk
because it shares the query's exact key concepts — "Papas," "Emeritus bloodline,"
and a shared "familial trait" — and then states the answer outright ("One eye is
green, and the other is white"). Ranks 2–5 are all loosely relevant: they're about
Papa Emeritus and the white eye too, which is why they were retrieved, but they
discuss the eye as *initiation* rather than the *bloodline trait* the question asks
about, so they sit noticeably farther away (0.47–0.50). This is good behavior — the
single chunk that directly answers the question wins clearly.

```
Query: "Who is Cardinal Copia in relation to Papa Nihil before he officially becomes Papa Emeritus IV?"

Top Results:
  Rank 1 | Distance: 0.2175 | Source: doc5.txt
  Papa Nihil is Papa Emeritus Zero (Nihil means 0). He is old and in not so great health (he tries to prove this wrong by attempting to play the saxophone, but Sister Imperator stops him, remember this). He is also the only Papa not played by Tobias. It is during his time as Papa (again) that the internet series "Chapters" was introduced. We learn through the chapters that Nihil and Sister Imperator used to have a thing. We are also introduced to a new character: Cardinal Copia.

  Rank 2 | Distance: 0.2313 | Source: doc6.txt
  Introduction of Cardinal Copia: How Sister met and made Nihil a Papa: Sister car crash: Old One calls: Important announcement and leaving hospital: 7" Of Satanic Panic flashback: Papa Nihil dying on stage & Copia becomes Papa IV: Technically Copia still isn't the leader, and he won't be until he's promoted. That's why we have Papa Nihil as our snoo! But other than that you did a really good job! It's a really old post, you're missing where Copia was promoted, had his run, and has now handed things over to Papa V. I'm also here trying to get a refresher before the full album drop, lol. Thank you for posting this!

  Rank 3 | Distance: 0.2590 | Source: doc6.txt
  (Not to be mistaken with Papa) Also, Cardinal Copia and Sister have an important announcement to make but we yet have to see what it is. - Prequelle era update 3 (Long overdue): After taking Sister out of the hospital we see Papa Nihil in the Clergy headquarters remembering his youth and longing for his days as the frontman of Ghost.We then see Nihil talk with Sister about Cardinal and given that he failed to win the Grammy, Nihil would like to have another shot at leading the band.Sister reminds Nihil about what happened last time.

  Rank 4 | Distance: 0.2682 | Source: doc5.txt
  Cardinal Copia is Papa Nihil's right hand and the second most recipient of the Employee of the Month award. He is clumsy, dorky, and a little timid. He rides an adult sized tricycle around the ministry. I'm gonna be a little biased, Cardinal Copia is my favorite. He will say or ask something out of pocket and finish it up with "Okie dokie." During Cardinal Copia's time, he wrote an album called Prequelle and did multiple tours, the last called The Ultimate Tour Named Death. It was during Cardi's time that we learn that the previous Papa's live in the ministry and Sister Imperator, Papa Nihil, and the clergy have them killed off and displayed in plexiglass coffins. If you had VIP tickets for the tours, you could go and see them in person (they were brought to each tour location). We also learned that back when Papa Nihil was still in his first run as Papa (late 1960s), he released an EP

  Rank 5 | Distance: 0.3070 | Source: doc5.txt
  refuses to call him Papa) than just clergy members. More chapters followed after that. We see that Papa Nihil is still around as a ghost, and we are introduced to Mr. Psaltarian. Once the world opened again, Papa started touring again. Because the Miasma bit in concert was such a hit with fans, they decided to keep it in the show with a brief resurrection via defibrillator. Through the chapters we learn that Copia is the bastard son of Sister Imperator and Papa Nihil (making Primo, Secondo, and Terzo his half brothers) and that Copia is aware that his time as Papa is running out, despite all of the success he has brought to the cause. All of this leads us to the movie: Rite Here, Rite Now. BELOW THIS CONTAINS SPOILERS FOR THE MOVIE
```

**Relevance explanation:** Every result here scores very low (0.22–0.31), meaning
strong matches — the query names "Cardinal Copia" and "Papa Nihil" explicitly, and
those exact proper nouns appear in all five chunks, so the embedding lands close.
The chunk that contains the precise expected answer ("Papa Nihil's right hand and
the second most recipient of the Employee of the Month award") is Rank 4 rather than
Rank 1, because Rank 1–3 mention *both* names more densely while Rank 4 is a longer,
more diluted chunk; all five are still well under 0.5, so the answer reaches the LLM.

```
Query: "What is the generally accepted etiquette for a heavy metal fan who wants to be near the stage but completely avoid moshing?"

Top Results:
  Rank 1 | Distance: 0.3240 | Source: doc8.txt
  2. General etiquette is to keep moshing limited to a circle, often with bigger guys standing at the perimeter to act as a shield for folks who don't want to participate. It should be easy to steer clear of if you don't want to be a part of it. If someone's being violent, moshing around people who don't want it, etc. other folks or security do often step in.

  Rank 2 | Distance: 0.3949 | Source: doc3.txt
  I had an interesting experience where people were getting rattled that others were moshing around them, getting upset about being bumped into etc.. Please let the mosh happen, or better yet, MAKE the mosh happen the band deserves the energy. The music has elements of metal and mosh pits are normal and encouraged, this isn't Taylor Swift. Getting bumped into at a metal show should not come as a surprise. If people are moshing around you and you're not game for it, just move to another spot. If you've never moshed before give it a try! You may love it. but yeah If you have general admission floor you are not entitled to stand in the same spot the entire night. keep it fluid, roll with the crowd, move to where you're comfortable and have fun!! The merch line was exceptionally long last time. I would jump in it as soon as possible if you want to get some.

  Rank 3 | Distance: 0.4333 | Source: doc8.txt
  I also use Eargasm Earplugs (although any high fidelity earplugs work!) high fidelity earplugs help filter out background noise (like audience clapping) and loud sounds (just muffles slightly) while still allowing you to hear the band really clearly (and people you're with) I use mine every concert, and I have had them for over a decade with no issues. But even the cheap foam ones would be a good idea! Some venues offer them in bathrooms or at concessions, sometimes for free, I wouldn't count on it. Otherwise, heavy metal concerts are fairly similar to things like a country concert, but with some key differences. 1. moshing will be happening! People will be dancing and swinging arms and legs, crashing into each other. If that's your vibe, you can join in! But remember that moshing isn't intended to hurt anyone!

  Rank 4 | Distance: 0.4428 | Source: doc9.txt
  if it was for a hardcore band that was probably me 😓 Love my spin kicks what can i say 🤷‍♂️ As it should be what would a slipknot pay be with out that and a wheel chair dude crowd surfing some shows should be hard like that others maybe chill out a bit it's not a slipknot / metal thing, it's a hardcore thing That's slam dancing. Normal at hardcore shows... Its hardcore fans thinking every pit is a hardcore pit. As soon as they start swinging in a metal core pit, I shove as many to the ground as possible. There's no rules, especially once you start swinging on the crowd You have my full support! I remember the old days of mosh where if someone went down, they were picked up.

  Rank 5 | Distance: 0.4800 | Source: doc9.txt
  I wish there were more people out there like you, it'd make aftershocks experience 10x better.🥲 Bless you and your hubby 😭🥰❤️❤️🤘🏽 I saw some dumbfuck chud today wearing a shirt that said Bitches be tripping, or maybe I just pushed one. Heads up, if that is your vibe, stay tf outta this festival please. That is not metal. That is far from metal. Being an asshole for fun ≠ metal ever Bro the fucking arms swinging all over is so stupid, I love the normal moshing when everyone is just pushing each other but dudes out there today were really tryna fuck shit up. Way too overkill. I saw one guy that literally started throwing leg kicks in the air like wtf!? if it was for a hardcore band that was probably me 😓 Love my spin kicks what can i say 🤷‍♂️
```

**Relevance explanation:** The top result (doc8.txt, 0.3240) is the precise answer:
it shares the query's core terms ("etiquette," "moshing," "near"/"perimeter") and
describes exactly the perimeter-shield convention asked about. Rank 2 (doc3.txt) is
genuinely relevant — "if you're not game for it, just move to another spot" — and
the LLM uses it. Ranks 3–5 are loosely relevant: they were retrieved because they're
all about pit behavior (earplugs, slam dancing, hardcore vs. metal), but they drift
toward other sub-topics, which is reflected in their higher distances (0.43–0.48).

---

## Grounded Generation

The model is Groq's `llama-3.3-70b-versatile`, called from `generation.py`. The exact
system prompt sent with every request is:

```
You are a helpful assistant for a guide about band lore and concert culture. Answer the user's question using ONLY the information provided in the documents below. Do not use any outside knowledge, and do not make assumptions beyond what the documents state. If the documents do not contain enough information to answer the question, respond with exactly: "I don't have enough information on that topic in the available documents."
```

**How it enforces grounding:** The instruction restricts the model with the word
**"ONLY"** ("using ONLY the information provided in the documents below"), explicitly
forbids outside knowledge and assumptions, and gives a **fixed fallback string** the
model must emit verbatim when the documents don't answer the question. The retrieved
chunks are injected into the user message under a `Documents:` header, each prefaced
with `[Source: docN.txt]`, so the model has clearly delimited context and nothing
else to draw from. Generation runs at `temperature=0` so the output stays tied to
that context rather than improvising.

**How source attribution is handled:** Sources are attached **programmatically**, not
by the model. In `generate()` the line `sources = sorted({chunk["source"] for chunk
in chunks})` derives the source list directly from the metadata of the retrieved
chunks, and that list is returned in the response dict alongside the answer. This is
more reliable than asking the model to self-cite because the citation can never be
hallucinated or omitted — it is computed from the chunks that were actually
retrieved, independent of whatever the LLM writes.

---

## Example Responses

```
Query: "According to the community lore, what specific physical trait is shared by all Papas from the Emeritus bloodline?"

Response:
According to the documents, all Papas from the Emeritus bloodline share a specific physical trait: one eye is green, and the other is white.

Sources: doc5.txt, doc6.txt, doc7.txt
```
*Traceable: the answer comes straight from doc5.txt #4 ("One eye is green, and the other is white") — it could not have been produced from general knowledge alone.*

```
Query: "What is the generally accepted etiquette for a heavy metal fan who wants to be near the stage but completely avoid moshing?"

Response:
According to the documents, general etiquette is to keep moshing limited to a circle, often with bigger guys standing at the perimeter to act as a shield for folks who don't want to participate. It should be easy to steer clear of if you don't want to be a part of it. If you're not game for moshing, you can just move to another spot. This suggests that fans who want to avoid moshing can do so by positioning themselves outside of the moshing circle or moving to a different area of the venue.

Sources: doc3.txt, doc8.txt, doc9.txt
```
*Traceable: the perimeter-shield detail is from doc8.txt #7 and the "move to another spot" advice is from doc3.txt #26 — both retrieved chunks.*

```
Query: "What is Taylor Swift's concert ticket cancellation policy?"

Response:
I don't have enough information on that topic in the available documents.

Sources: (none)
```
*Fallback correctly triggered: the corpus is only Sleep Token / Ghost / Rob Zombie threads, so no chunk scored below the 0.5 relevance gate and the pipeline returned the fallback without calling the LLM (`chunks_used = 0`). The query is out-of-scope because nothing in the documents discusses Taylor Swift or ticket-cancellation policy.*

---

## Query Interface

Built with Gradio (`app.py`). Layout:

- **Input — "Your question"** (single-line textbox): the user types a free-text
  question about Ghost, Sleep Token, or Rob Zombie lore / concert culture. A
  placeholder shows an example question.
- **"Ask" button**: submits the question. Pressing **Enter** in the textbox submits
  it too.
- **Output — "Answer"** (8-line textbox): the grounded answer (or the fallback
  message). Empty input returns "Please enter a question."
- **Output — "Retrieved from"** (4-line textbox): a bullet list of the source
  filenames the answer was drawn from.

Sample interaction as it appears in the UI:

```
Your question: According to the community lore, what specific physical trait is shared by all Papas from the Emeritus bloodline?
[Ask]

Answer:
According to the documents, all Papas from the Emeritus bloodline share a specific physical trait: one eye is green, and the other is white.

Retrieved from:
• doc5.txt
• doc6.txt
• doc7.txt
```

Run with `python app.py` (use the project's `.venv`) and open the printed local URL
(http://localhost:7860, or the next free port).

---

## Evaluation Report

```
Q#  | Question (abbreviated)                  | Judgment
----|-----------------------------------------|-------------------
1   | Papas' shared physical trait            | ACCURATE
2   | "Atlantic" hospital meaning             | ACCURATE
3   | Cardinal Copia vs. Papa Nihil           | ACCURATE
4   | Near-stage, avoid-moshing etiquette     | ACCURATE
5   | Cell-phone advice at Sleep Token shows  | INACCURATE
----|-----------------------------------------|-------------------
    | Results: 4 accurate, 0 partial, 1 inaccurate
```

```
Q1: "According to the community lore, what specific physical trait is shared by all Papas from the Emeritus bloodline?"
Expected:  They all have one green eye and one white eye.
Response:  According to the documents, all Papas from the Emeritus bloodline share a specific physical trait: one eye is green, and the other is white.
Judgment:  ACCURATE
Reasoning: Exact match, reproduced from doc5.txt #4 (top result, distance 0.3776) with no added outside detail.

Q2: "In the track-by-track lore breakdown, what does Vessel waking up in a hospital in the song \"Atlantic\" signify regarding his connection to Sleep?"
Expected:  It signifies a failed suicide attempt meant to sever his connection with the deity Sleep.
Response:  Vessel waking up in a hospital in the song "Atlantic" signifies that he had a failed suicide attempt, perhaps to sever his connection with Sleep.
Judgment:  ACCURATE
Reasoning: Matches the expected answer and is traceable verbatim to doc1.txt #12; the model kept the source's "perhaps" hedge instead of overstating certainty.

Q3: "Who is Cardinal Copia in relation to Papa Nihil before he officially becomes Papa Emeritus IV?"
Expected:  He is Papa Nihil's right-hand man and the second most frequent recipient of the Employee of the Month award.
Response:  According to the documents, Cardinal Copia is Papa Nihil's right-hand man and the second most recipient of the Employee of the Month award. Additionally, it is revealed through the chapters that Cardinal Copia is the bastard son of Sister Imperator and Papa Nihil.
Judgment:  ACCURATE
Reasoning: Contains the full expected answer (doc5.txt #8). The extra "bastard son" sentence is also grounded in a retrieved chunk (doc5.txt #12), so it's correct added context, not a hallucination.

Q4: "What is the generally accepted etiquette for a heavy metal fan who wants to be near the stage but completely avoid moshing?"
Expected:  Keep to the perimeter of the circle pit, where bigger fans typically stand to act as a physical shield for those who don't want to participate.
Response:  According to the documents, general etiquette is to keep moshing limited to a circle, often with bigger guys standing at the perimeter to act as a shield for folks who don't want to participate. It should be easy to steer clear of if you don't want to be a part of it. If you're not game for moshing, you can just move to another spot.
Judgment:  ACCURATE
Reasoning: Matches expected; the perimeter-shield detail is from doc8.txt #7 (top result, 0.3240) and the "move to another spot" addition is from doc3.txt #26, also retrieved.

Q5: "What specific piece of advice do veteran fans repeatedly give regarding cell phone usage at Sleep Token rituals?"
Expected:  Do not record the entire show or watch the concert through your screen; take a few photos and put the phone down to actually experience the show.
Response:  I don't have enough information on that topic in the available documents.
Judgment:  INACCURATE
Reasoning: False negative — the answer is in doc4.txt #0 and doc3.txt #25, but those chunks were retrieved only at ranks 4-5 with distances above the 0.5 gate (0.5985, 0.6091), so the pipeline returned the fallback. See Failure Case Analysis.
```

---

## Failure Case Analysis

```
Failure case: Question 5 — "What specific piece of advice do veteran fans
repeatedly give regarding cell phone usage at Sleep Token rituals?"

Observed failure:
The system returned the out-of-scope fallback ("I don't have enough information
on that topic in the available documents") for a question the documents DO
answer. Expected: don't record the whole show / phone down, be present.

Pipeline stage: Both — retrieval (weak ranking) and the generation-gate
threshold that acts on it.

Specific cause:
The relevant advice lives in chunks that are mostly about other topics — doc4.txt
#0 mixes "Phone down hands up" with merch-line and hydration chatter, and doc3.txt
#25 buries "don't hold your phone high above your head" inside general show
etiquette. That dilution, plus a vocabulary gap between the formal query ("cell
phone usage at Sleep Token rituals," "veteran fans") and the casual source text
("phone," "concert," "show"), pushed every cosine distance above 0.5 (range
0.5557-0.6091). The < 0.5 fallback gate in ask() then filtered out all five
retrieved chunks and short-circuited to the fallback before calling the LLM.

Evidence:
retrieve(Q5, k=5) distances and sources:
  Rank 1 | 0.5557 | doc2.txt #1  (Sleep = Death theory — off topic)
  Rank 2 | 0.5744 | doc1.txt #24 (Sleep as addiction metaphor — off topic)
  Rank 3 | 0.5795 | doc1.txt #0  (lore intro — off topic)
  Rank 4 | 0.5985 | doc3.txt #25 ("If you must film... don't hold your phone high
                                   above your head... Just be present")  <-- relevant
  Rank 5 | 0.6091 | doc4.txt #0  ("Don't record the entire concert on your phone...
                                   Phone down hands up!")                <-- the answer
The correct content was retrieved (ranks 4-5) but scored just above the 0.5 cutoff.

What would fix it:
Raise the ask() fallback gate from 0.5 to ~0.65 and let the LLM's grounding
instruction handle borderline cases. At 0.65, doc4.txt #0 (0.6091) and doc3.txt #25
(0.5985) would reach the model, which can then extract the phone-down advice. The
out-of-scope Taylor Swift query would still be rejected by the system prompt's
explicit fallback instruction even if it passed the looser numeric gate.
```

---

## Spec Reflection

**One way the spec helped during implementation:** The Chunking Strategy section of
`planning.md` argued that my sources are "long, multi-sentence paragraphs explaining
complex lore" and that splitting too aggressively would "cut a theory in half." That
written reasoning is exactly why, when my first chunker collapsed everything into a
fixed-character stream and started chunks mid-word, I rejected it and moved to
paragraph-aware chunking that keeps whole comments intact. The payoff is visible in
retrieval: the chunk that answers Q1 (doc5.txt #4) contains the complete statement
"They all have a familial trait: their eyes. One eye is green, and the other is
white" in one piece, so a single top-ranked chunk carries the full answer rather
than half of it.

**One way the implementation diverged from the spec:** `planning.md` never mentioned
a numeric relevance gate — it assumed grounding would come entirely from the system
prompt. In practice, during Milestone 5 I added a hard rule in `ask()`: if no
retrieved chunk scores below 0.5 cosine distance, return the fallback without calling
the LLM. I added this because relying on the model alone to self-censor felt risky
for out-of-scope questions. It works well for clearly off-topic queries (the Taylor
Swift test), but it also caused my one evaluation failure (Q5), where genuinely
relevant chunks scored 0.59–0.61 and were filtered out. The divergence was the right
instinct (defense in depth against hallucination) with the wrong threshold; the fix
in the failure analysis is to loosen the gate to ~0.65 and lean on the prompt for the
borderline band.

---

## AI Usage

```
Instance 1:
Task:         Asked Claude (Claude Code) to implement the Milestone 3 ingestion +
              chunking from my planning.md spec: load doc1-10.txt, strip Reddit
              boilerplate, and chunk at my target size/overlap.
Output:       A working chunk_documents.py, but its first version collapsed ALL
              whitespace (including paragraph breaks) into one stream and produced
              fixed-character chunks that started and ended mid-word.
Intervention: I directed it to (a) switch to paragraph-aware chunking that packs
              whole Reddit comments and only word-splits when a single comment
              exceeds the limit, and (b) preserve paragraph boundaries during
              cleaning. I also bumped the size/overlap from 800/150 to 900/175.
```

```
Instance 2:
Task:         Asked Claude to drop non-English comments before embedding, since
              all-MiniLM-L6-v2 is English-centric and the threads contain Spanish.
Output:       A first version using langdetect's detect() with a 40-character
              threshold. It correctly dropped a long Spanish comment but ALSO
              wrongly dropped short English lines — e.g. it tagged '2016 "Square
              Hammer" Best Metal Video Won' as German at 0.9999 confidence.
Intervention: I had it make the filter conservative: only judge paragraphs >= 60
              characters, only drop when the top language is non-English with >= 0.90
              confidence AND English isn't a candidate. That kept the three false-
              positive English lines and still removed the real Spanish comment.
```

```
Instance 3:
Task:         Asked Claude to wire embedding + retrieval into ChromaDB for Milestone 4.
Output:       A retrieval.py that worked, but would have used Chroma's default L2
              distance space, whose magnitudes aren't comparable to the < 0.5
              relevance threshold the rubric uses.
Intervention: I had it create the collection with metadata={"hnsw:space": "cosine"}
              so distances are interpretable cosine scores, which is what every
              distance in this README and evaluation_results.txt now reports.
```
