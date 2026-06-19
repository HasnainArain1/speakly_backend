"""
Groq API service for AI-powered features:
- Voice conversation (LLaMA 3 8B)
- End-session reports (LLaMA 3 70B)
- Speech-to-text (Whisper)
- Quiz generation
- Tense exercises
"""

import json
import os
import logging
from typing import List, Optional
from groq import Groq
from dotenv import load_dotenv

logger = logging.getLogger("speakly")

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
try:
    client = Groq(api_key=GROQ_API_KEY or "gsk_placeholder")
except Exception:
    client = None

# Model configuration
CONVERSATION_MODEL = "llama-3.1-8b-instant"
REPORT_MODEL = "llama-3.3-70b-versatile"
WHISPER_MODEL = "whisper-large-v3"

FALLBACK_MODAL_EXERCISES = {
    "can": [
        {"sentence": "I ___ speak English fluently.", "answer": "can", "explanation": "Use 'can' to express present ability."},
        {"sentence": "She can ___ a song beautifully.", "answer": "sing", "explanation": "After 'can', use the base form of the verb."},
        {"sentence": "___ you help me with this task, please?", "answer": "Can", "explanation": "Use 'Can' at the start of a sentence to make an informal request."},
        {"sentence": "He can write ___ than his brother.", "answer": "faster", "explanation": "Comparison adjective used with modal capability."},
        {"sentence": "You can eat ___ you want from the menu.", "answer": "whatever", "explanation": "Pronoun completes the phrase indicating permission."}
    ],
    "could": [
        {"sentence": "When I was young, I ___ run very fast.", "answer": "could", "explanation": "Use 'could' to express past ability."},
        {"sentence": "She could ___ the answer yesterday.", "answer": "find", "explanation": "After 'could', use the base form of the verb."},
        {"sentence": "___ you please pass the salt?", "answer": "Could", "explanation": "Use 'Could' to make a polite, formal request."},
        {"sentence": "If we had more money, we could ___ a new car.", "answer": "buy", "explanation": "Condition indicates past/hypothetical capability."},
        {"sentence": "They could not arrive ___ because of the rain.", "answer": "early", "explanation": "Adverb modifying the verb 'arrive' under limitation."}
    ],
    "may": [
        {"sentence": "___ I come in, teacher?", "answer": "May", "explanation": "Use 'May' to ask for formal permission."},
        {"sentence": "It may ___ rain tonight.", "answer": "well", "explanation": "Use 'may' to express high possibility of rain."},
        {"sentence": "She may ___ to the market later.", "answer": "go", "explanation": "After 'may', use the base form of the verb."},
        {"sentence": "May all your dreams ___ true!", "answer": "come", "explanation": "Expresses a wish or blessing using base verb."},
        {"sentence": "The store may close ___ than usual today.", "answer": "earlier", "explanation": "Adverb showing potential earlier schedule."}
    ],
    "might": [
        {"sentence": "We ___ go to Murree if the weather is nice.", "answer": "might", "explanation": "Use 'might' for weak possibility."},
        {"sentence": "He might ___ his keys at the office.", "answer": "have", "explanation": "Use 'might have' to express past possibility."},
        {"sentence": "They might not ___ the news yet.", "answer": "know", "explanation": "After 'might', use the base form of the verb."},
        {"sentence": "It might be ___ to leave now before it gets dark.", "answer": "better", "explanation": "Comparative adjective for advice/possibility."},
        {"sentence": "She might buy the dress ___ it is too expensive.", "answer": "unless", "explanation": "Conjunction shows condition of weak possibility."}
    ],
    "must": [
        {"sentence": "You ___ wear a helmet while riding a bike.", "answer": "must", "explanation": "Use 'must' for strong obligation or rules."},
        {"sentence": "Students must ___ their homework daily.", "answer": "do", "explanation": "After 'must', use the base form of the verb."},
        {"sentence": "The ground is wet; it must ___ rained last night.", "answer": "have", "explanation": "Use 'must have' for logical deduction about the past."},
        {"sentence": "We must protect ___ environment.", "answer": "our", "explanation": "Possessive pronoun fits the sentence of obligation."},
        {"sentence": "You must not make ___ noise in the library.", "answer": "any", "explanation": "Determiner showing absolute prohibition."}
    ],
    "should": [
        {"sentence": "You ___ eat more fruits and vegetables.", "answer": "should", "explanation": "Use 'should' to give advice or recommendations."},
        {"sentence": "We should ___ respectful to our teachers.", "answer": "be", "explanation": "After 'should', use the base form of the verb."},
        {"sentence": "Should we start the meeting ___?", "answer": "now", "explanation": "Adverb asking about the appropriate time for recommendation."},
        {"sentence": "They should drive ___ in the school zone.", "answer": "slowly", "explanation": "Adverb modifying recommended driving speed."},
        {"sentence": "He should write the email ___ instead of calling.", "answer": "himself", "explanation": "Reflexive pronoun highlights personal recommendation."}
    ],
    "would": [
        {"sentence": "___ you like a cup of tea?", "answer": "Would", "explanation": "Use 'Would you like' to make a polite offer."},
        {"sentence": "If I won the lottery, I ___ travel the world.", "answer": "would", "explanation": "Use 'would' in conditional sentences for hypothetical results."},
        {"sentence": "She would ___ to play badminton tomorrow.", "answer": "love", "explanation": "After 'would', use base verb to express preference."},
        {"sentence": "My grandfather would always ___ us stories in winter.", "answer": "tell", "explanation": "Use 'would' to describe a past habit/routine."},
        {"sentence": "They would not agree to the plan ___ we offered money.", "answer": "even", "explanation": "Adverbial modifier for conditional hypothetical."}
    ],
    "shall": [
        {"sentence": "___ we go for a walk?", "answer": "Shall", "explanation": "Use 'Shall' to make suggestions or offers with 'I' or 'we'."},
        {"sentence": "I shall ___ you at the station.", "answer": "meet", "explanation": "After 'shall', use the base form of the verb."},
        {"sentence": "We shall overcome ___ difficulties together.", "answer": "all", "explanation": "Quantifier completes the statement of future resolve."},
        {"sentence": "What shall I ___ for dinner tonight?", "answer": "cook", "explanation": "Base verb for asking recommendations."},
        {"sentence": "The contract shall ___ valid for one year.", "answer": "remain", "explanation": "Base verb expressing formal rule/status."}
    ],
    "will": [
        {"sentence": "I ___ call you tomorrow morning.", "answer": "will", "explanation": "Use 'will' to express future plans or promises."},
        {"sentence": "It will ___ hot in Lahore during June.", "answer": "be", "explanation": "After 'will', use the base form of the verb."},
        {"sentence": "Will you ___ the door for me?", "answer": "open", "explanation": "Base verb in polite future request."},
        {"sentence": "They will arrive ___ midnight.", "answer": "before", "explanation": "Preposition of time indicating target future limit."},
        {"sentence": "She will complete the project ___ next week.", "answer": "by", "explanation": "Preposition of deadline completes the future action."}
    ]
}

FALLBACK_GRAMMAR_EXERCISES = {
    "prepositions": [
        {"sentence": "The book is ___ the table.", "answer": "on", "explanation": "Use 'on' for surface contact prepositions of place."},
        {"sentence": "We will meet ___ 5:00 PM.", "answer": "at", "explanation": "Use 'at' for precise clock times."},
        {"sentence": "He was born ___ January.", "answer": "in", "explanation": "Use 'in' for months, years, and seasons."},
        {"sentence": "She walked ___ the classroom quietly.", "answer": "into", "explanation": "Use 'into' to show movement towards the inside of a space."},
        {"sentence": "They went to the market ___ car.", "answer": "by", "explanation": "Use 'by' to show the mode of transportation."}
    ],
    "voice": [
        {"sentence": "The cake was ___ by my mother.", "answer": "baked", "explanation": "Passive voice uses past participle form of the main verb."},
        {"sentence": "He ___ a letter to his friend yesterday.", "answer": "wrote", "explanation": "Active voice with simple past tense."},
        {"sentence": "Active: She sings a song. Passive: A song ___ sung by her.", "answer": "is", "explanation": "Present simple passive uses 'is/are' + V3."},
        {"sentence": "A beautiful picture was ___ by the student.", "answer": "drawn", "explanation": "Past participle form of 'draw' in passive voice."},
        {"sentence": "Passive: The match is being played. Active: They are ___ the match.", "answer": "playing", "explanation": "Present continuous active uses V-ing."}
    ],
    "speech": [
        {"sentence": "Direct: He said, 'I am tired.' Indirect: He said that he ___ tired.", "answer": "was", "explanation": "Simple present in direct speech changes to simple past in indirect speech."},
        {"sentence": "She asked ___ I wanted to go with her.", "answer": "if", "explanation": "Use 'if' or 'whether' for yes/no questions in indirect speech."},
        {"sentence": "Direct: 'Go away!' Indirect: He ordered me ___ go away.", "answer": "to", "explanation": "Imperative sentences in indirect speech use infinitive 'to'."},
        {"sentence": "He told me that he ___ done his homework.", "answer": "had", "explanation": "Present perfect in direct speech changes to past perfect in indirect speech."},
        {"sentence": "Direct: 'I will write.' Indirect: She said she ___ write.", "answer": "would", "explanation": "Future 'will' changes to conditional 'would' in indirect speech."}
    ],
    "conditionals": [
        {"sentence": "If it rains, we ___ stay at home.", "answer": "will", "explanation": "First conditional uses Present Simple in the if-clause and future 'will' in the result clause."},
        {"sentence": "If I ___ you, I would study harder.", "answer": "were", "explanation": "Second conditional uses 'were' for the verb 'to be' regardless of the subject pronoun."},
        {"sentence": "If you heat water to 100 degrees, it ___.", "answer": "boils", "explanation": "Zero conditional (scientific fact) uses present simple in both clauses."},
        {"sentence": "If she had studied, she ___ have passed the test.", "answer": "would", "explanation": "Third conditional uses 'would have' + V3 in the result clause."},
        {"sentence": "We would travel more if we ___ more free time.", "answer": "had", "explanation": "Second conditional uses simple past in the condition clause."}
    ],
    "articles": [
        {"sentence": "She wants to buy ___ new dress.", "answer": "a", "explanation": "Use article 'a' before singular countable nouns beginning with consonant sounds."},
        {"sentence": "He is ___ honest student.", "answer": "an", "explanation": "Use article 'an' before words beginning with silent 'h' and vowel sounds."},
        {"sentence": "___ sun rises in the east.", "answer": "The", "explanation": "Use the definite article 'the' for unique celestial bodies."},
        {"sentence": "They visited ___ Himalayas last summer.", "answer": "the", "explanation": "Use 'the' before names of mountain ranges."},
        {"sentence": "We saw an elephant and ___ monkey at the zoo.", "answer": "a", "explanation": "Use 'a' for singular noun with consonant sound."}
    ],
    "comparison": [
        {"sentence": "Ali is taller ___ Ahmed.", "answer": "than", "explanation": "Use 'than' for comparative degree comparison."},
        {"sentence": "Mount Everest is the ___ mountain in the world.", "answer": "highest", "explanation": "Superlative degree requires definite article 'the' and suffix '-est'."},
        {"sentence": "This puzzle is more ___ than the last one.", "answer": "difficult", "explanation": "Use 'more' + base adjective for comparative degree of longer adjectives."},
        {"sentence": "She is the ___ intelligent girl in our class.", "answer": "most", "explanation": "Superlative degree of longer adjectives uses 'most'."},
        {"sentence": "Your handwriting is ___ than mine.", "answer": "better", "explanation": "Comparative degree of irregular adjective 'good' is 'better'."}
    ],
    "general": [
        {"sentence": "They ___ learning English grammar now.", "answer": "are", "explanation": "Present continuous plural subject verb agreement."},
        {"sentence": "She ___ completed her project yesterday.", "answer": "had", "explanation": "Past perfect auxiliary verb usage."},
        {"sentence": "Every student ___ to submit their assignment.", "answer": "has", "explanation": "Singular subject agreement with distributive pronoun."},
        {"sentence": "We went to the beach ___ the cold weather.", "answer": "despite", "explanation": "Preposition expressing contrast."},
        {"sentence": "He walks to school ___ day.", "answer": "every", "explanation": "Determiner showing regular frequency."}
    ]
}

FALLBACK_GRAMMAR_CONTENT = {
    "prepositions": {
        "explanation": "Prepositions are words that show relationships between nouns, pronouns, and other words in a sentence, specifying time, place, or direction.",
        "examples": [
            "The cat is sleeping under the bed.",
            "Our school starts at 8:00 AM.",
            "They will travel to Lahore in December.",
            "She put the keys on the counter.",
            "We walked through the beautiful park."
        ],
        "exercises": FALLBACK_GRAMMAR_EXERCISES["prepositions"]
    },
    "voice": {
        "explanation": "Voice indicates whether the subject of the sentence performs the action (Active) or receives the action (Passive).",
        "examples": [
            "Active: The teacher explains the lesson.",
            "Passive: The lesson is explained by the teacher.",
            "Active: She bought a new pen.",
            "Passive: A new pen was bought by her.",
            "Passive: The work will be done tomorrow."
        ],
        "exercises": FALLBACK_GRAMMAR_EXERCISES["voice"]
    },
    "speech": {
        "explanation": "Direct speech repeats the exact words spoken, while indirect (reported) speech reports the content of what was said without repeating the exact words.",
        "examples": [
            "Direct: He said, 'I am learning English.'",
            "Indirect: He said that he was learning English.",
            "Direct: She asked, 'Are you coming?'",
            "Indirect: She asked if I was coming.",
            "Indirect: The doctor advised him to take medicine."
        ],
        "exercises": FALLBACK_GRAMMAR_EXERCISES["speech"]
    },
    "conditionals": {
        "explanation": "Conditional sentences describe hypothetical or real scenarios and their consequences using different tenses based on probability.",
        "examples": [
            "If it rains, we will cancel the trip.",
            "If I were you, I would read more books.",
            "If you freeze water, it becomes solid.",
            "If they had run fast, they would have caught the bus.",
            "We will stay indoors if the weather is bad."
        ],
        "exercises": FALLBACK_GRAMMAR_EXERCISES["conditionals"]
    },
    "articles": {
        "explanation": "Articles (a, an, the) are determiners used to specify whether a noun is indefinite (any general item) or definite (a specific known item).",
        "examples": [
            "I saw a bird on the tree.",
            "He wants to eat an apple.",
            "The moon shines brightly at night.",
            "She is an honorable citizen of Pakistan.",
            "We visited the historic Badshahi Mosque."
        ],
        "exercises": FALLBACK_GRAMMAR_EXERCISES["articles"]
    },
    "comparison": {
        "explanation": "Degrees of comparison (positive, comparative, superlative) are used to compare characteristics of different nouns or actions.",
        "examples": [
            "This room is larger than the other one.",
            "Mount K2 is the second highest peak.",
            "She is as smart as her sister.",
            "Health is more valuable than wealth.",
            "He is the best cricket player in our team."
        ],
        "exercises": FALLBACK_GRAMMAR_EXERCISES["comparison"]
    },
    "general": {
        "explanation": "Grammar rules help structure sentences correctly, ensuring subject-verb agreement, proper tense usage, and clarity.",
        "examples": [
            "They are practicing their speech now.",
            "She completed all tasks before leaving.",
            "Every student has submitted the work.",
            "We decided to walk despite the rain.",
            "He speaks English fluently and confidently."
        ],
        "exercises": FALLBACK_GRAMMAR_EXERCISES["general"]
    }
}

FALLBACK_TENSE_EXERCISES = {
    "present simple": [
        {"sentence": "Every morning, he ___ to the park.", "answer": "walks", "explanation": "Third-person singular 'he' in Present Simple takes the verb with an 's' suffix."},
        {"sentence": "The sun ___ in the east.", "answer": "rises", "explanation": "Scientific/universal facts are stated in the Present Simple tense."},
        {"sentence": "Water ___ at 100 degrees Celsius.", "answer": "boils", "explanation": "For general truth, we use present simple singular verb."},
        {"sentence": "They ___ not like coffee.", "answer": "do", "explanation": "Plural negative in present simple uses auxiliary 'do'."},
        {"sentence": "Does she ___ English fluently?", "answer": "speak", "explanation": "After 'does', the main verb remains in base form."}
    ],
    "present continuous": [
        {"sentence": "Look! The children ___ playing in the garden.", "answer": "are", "explanation": "Present continuous uses am/is/are + verb-ing. Plural subject uses 'are'."},
        {"sentence": "I am ___ for my exams right now.", "answer": "studying", "explanation": "Present continuous V-ing form of 'study'."},
        {"sentence": "She ___ cooking dinner at the moment.", "answer": "is", "explanation": "Singular subject uses 'is' in present continuous."},
        {"sentence": "Why are you ___ at me?", "answer": "looking", "explanation": "Continuous V-ing form following 'are'."},
        {"sentence": "It is not ___ outside today.", "answer": "raining", "explanation": "Negative present continuous indicates action in progress."}
    ],
    "present perfect": [
        {"sentence": "I ___ already finished my homework.", "answer": "have", "explanation": "Present perfect uses have/has + past participle (V3). 'I' takes 'have'."},
        {"sentence": "She has ___ to Karachi three times.", "answer": "been", "explanation": "Past participle form of 'go/be' is 'been'."},
        {"sentence": "They have not ___ the news yet.", "answer": "heard", "explanation": "Past participle V3 form of 'hear'."},
        {"sentence": "He ___ lived in this city since 2010.", "answer": "has", "explanation": "Third person singular uses 'has' in present perfect."},
        {"sentence": "Have you ever ___ a horse?", "answer": "ridden", "explanation": "Past participle V3 form of 'ride'."}
    ],
    "present perfect continuous": [
        {"sentence": "She has ___ studying for three hours.", "answer": "been", "explanation": "Present perfect continuous uses has/have + been + verb-ing."},
        {"sentence": "They have been ___ cricket since morning.", "answer": "playing", "explanation": "Continuous V-ing form after 'have been'."},
        {"sentence": "I ___ been waiting here since 4 o'clock.", "answer": "have", "explanation": "Subject 'I' takes auxiliary 'have'."},
        {"sentence": "It has ___ raining all night.", "answer": "been", "explanation": "Singular subject present perfect continuous form."},
        {"sentence": "We have been living in Lahore ___ five years.", "answer": "for", "explanation": "Use 'for' to denote a duration of time."}
    ],
    "past simple": [
        {"sentence": "Yesterday, we ___ a movie.", "answer": "watched", "explanation": "Simple past of regular verb 'watch' is 'watched'."},
        {"sentence": "She ___ to the market two hours ago.", "answer": "went", "explanation": "Simple past of irregular verb 'go' is 'went'."},
        {"sentence": "They did not ___ the game last week.", "answer": "play", "explanation": "After 'did not', the verb returns to base form."},
        {"sentence": "Where ___ you meet him yesterday?", "answer": "did", "explanation": "Question auxiliary for past simple is 'did'."},
        {"sentence": "He ___ the piano beautifully at the concert.", "answer": "played", "explanation": "Past simple indicates completed past action."}
    ],
    "past continuous": [
        {"sentence": "While she was cooking, the phone ___.", "answer": "rang", "explanation": "Interrupting action uses past simple while background action uses past continuous."},
        {"sentence": "They ___ playing football when it started to rain.", "answer": "were", "explanation": "Past continuous uses was/were + verb-ing. Plural subject uses 'were'."},
        {"sentence": "I ___ studying when you called.", "answer": "was", "explanation": "Subject 'I' takes 'was' in past continuous."},
        {"sentence": "What were you ___ at 8 PM yesterday?", "answer": "doing", "explanation": "Verb-ing form following past auxiliary 'were'."},
        {"sentence": "She was not ___ attention to the lecture.", "answer": "paying", "explanation": "V-ing form for continuous action in the past."}
    ],
    "past perfect": [
        {"sentence": "When we arrived, the train had already ___.", "answer": "left", "explanation": "Past perfect uses had + past participle (V3) for the earlier of two past actions."},
        {"sentence": "She ___ not finished her test when the bell rang.", "answer": "had", "explanation": "Negative past perfect auxiliary is 'had'."},
        {"sentence": "After they had ___ dinner, they went to sleep.", "answer": "eaten", "explanation": "Past participle V3 of 'eat' is 'eaten'."},
        {"sentence": "He had ___ all his work before the teacher checked.", "answer": "done", "explanation": "Past participle V3 of 'do' is 'done'."},
        {"sentence": "Had you ___ him before you met him yesterday?", "answer": "seen", "explanation": "Past participle V3 of 'see' is 'seen'."}
    ],
    "past perfect continuous": [
        {"sentence": "He had ___ working for ten hours before he slept.", "answer": "been", "explanation": "Past perfect continuous uses had + been + verb-ing."},
        {"sentence": "They had been ___ since morning before the match was cancelled.", "answer": "playing", "explanation": "Continuous V-ing form after 'had been'."},
        {"sentence": "She ___ been practicing the piano before she performed.", "answer": "had", "explanation": "Past perfect continuous auxiliary for all subjects is 'had'."},
        {"sentence": "We had been living there ___ three years before moving.", "answer": "for", "explanation": "Use 'for' to indicate duration of past continuous action."},
        {"sentence": "It had been ___ heavily before the sun came out.", "answer": "raining", "explanation": "V-ing continuous verb form."}
    ],
    "future simple": [
        {"sentence": "I ___ travel to Karachi next week.", "answer": "will", "explanation": "Use 'will' to express simple future plans or predictions."},
        {"sentence": "They will ___ their results tomorrow.", "answer": "get", "explanation": "After 'will', use the base form of the verb."},
        {"sentence": "Will she ___ to our party?", "answer": "come", "explanation": "Base verb in future simple question."},
        {"sentence": "The weather ___ be hot tomorrow.", "answer": "will", "explanation": "Future simple prediction."},
        {"sentence": "We will not ___ our class on Sunday.", "answer": "have", "explanation": "Negative future simple verb base form."}
    ],
    "future continuous": [
        {"sentence": "At this time tomorrow, I will ___ flying to London.", "answer": "be", "explanation": "Future continuous uses will + be + verb-ing."},
        {"sentence": "They will be ___ cricket at 4 PM tomorrow.", "answer": "playing", "explanation": "Continuous V-ing form after 'will be'."},
        {"sentence": "She ___ be studying when you arrive.", "answer": "will", "explanation": "Future continuous auxiliary 'will'."},
        {"sentence": "Will you be ___ tonight?", "answer": "working", "explanation": "V-ing form in future continuous question."},
        {"sentence": "We will be ___ dinner when they reach our home.", "answer": "having", "explanation": "Continuous action in progress in the future."}
    ],
    "future perfect": [
        {"sentence": "By next month, I will have ___ my graduation.", "answer": "completed", "explanation": "Future perfect uses will + have + past participle (V3)."},
        {"sentence": "She will ___ finished her project by Friday.", "answer": "have", "explanation": "Future perfect auxiliary is 'will have'."},
        {"sentence": "They will have ___ their home by evening.", "answer": "reached", "explanation": "Past participle V3 of 'reach' is 'reached'."},
        {"sentence": "By 2030, scientists will have ___ a cure.", "answer": "found", "explanation": "Past participle V3 of 'find' is 'found'."},
        {"sentence": "Will you have ___ the book by tomorrow?", "answer": "read", "explanation": "Past participle V3 of 'read' is 'read' (pronounced red)."}
    ],
    "future perfect continuous": [
        {"sentence": "By next year, I will have ___ living here for five years.", "answer": "been", "explanation": "Future perfect continuous uses will + have + been + verb-ing."},
        {"sentence": "She will have been ___ English for a decade by graduation.", "answer": "studying", "explanation": "Continuous V-ing form after 'will have been'."},
        {"sentence": "They will have ___ playing for three hours by sunset.", "answer": "been", "explanation": "Future perfect continuous indicator."},
        {"sentence": "We ___ have been working here for six months by December.", "answer": "will", "explanation": "Future perfect continuous helper verb."},
        {"sentence": "By midnight, it will have been ___ for twelve hours.", "answer": "raining", "explanation": "V-ing form indicating continuous duration in future."}
    ],
    "general": [
        {"sentence": "They ___ learning English grammar now.", "answer": "are", "explanation": "Present continuous plural subject verb agreement."},
        {"sentence": "She ___ completed her project yesterday.", "answer": "had", "explanation": "Past perfect auxiliary verb usage."},
        {"sentence": "Every student ___ to submit their assignment.", "answer": "has", "explanation": "Singular subject agreement with distributive pronoun."},
        {"sentence": "We went to the beach ___ the cold weather.", "answer": "despite", "explanation": "Preposition expressing contrast."},
        {"sentence": "He walks to school ___ day.", "answer": "every", "explanation": "Determiner showing regular frequency."}
    ]
}


async def transcribe_audio(audio_file) -> dict:
    """
    Transcribe audio to text using Groq Whisper API.
    
    Args:
        audio_file: Audio file object from upload.
    
    Returns:
        Dict with 'text' and 'language' keys.
    """
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.webm", audio_file, "audio/webm"),
            model=WHISPER_MODEL,
            response_format="verbose_json",
        )
        
        text = ""
        language = None
        
        if hasattr(transcription, "text"):
            text = transcription.text
        elif isinstance(transcription, dict) and "text" in transcription:
            text = transcription["text"]
            
        if hasattr(transcription, "language"):
            language = transcription.language
        elif isinstance(transcription, dict) and "language" in transcription:
            language = transcription["language"]
            
        return {"text": text, "language": language}
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")


async def get_conversation_response(
    conversation: List[dict],
    topic: str = "Daily Life",
    difficulty: str = "intermediate"
) -> str:
    """
    Get AI tutor response in a conversation using sliding window.
    Sends only last 8 messages to stay within token limits.
    
    Args:
        conversation: Full conversation history.
        topic: Conversation topic.
        difficulty: Student's level.
    
    Returns:
        AI response text.
    """
    system_prompt = f"""=== YOUR IDENTITY (always use this when asked about yourself) ===
Your name is Aria.
You are a friendly AI English conversation tutor, created by the Speakly team.
Your purpose is to help Pakistani students improve their spoken English through natural, everyday conversations.
You are warm, patient, and encouraging — like a supportive older sister who genuinely wants to help.
If anyone asks "Who are you?", "What is your name?", or anything about yourself, ALWAYS respond with your name (Aria), your role (English conversation tutor at Speakly), and that you're here to help them practice and improve their English through fun conversations.
Never invent a different name or backstory. You are always Aria from Speakly.

=== CONVERSATION RULES ===
1. Have a natural English conversation on the given topic.
2. NEVER correct the student mid-conversation — let them finish and keep the flow going.
3. Respond naturally and ask follow-up questions to encourage more speaking.
4. Keep responses between 2 to 3 sentences — not too short, not too long. Give enough detail to keep the conversation interesting and educational.
5. If the student writes in Urdu, gently say: "Try to say that in English — I believe in you!"
6. Be warm, encouraging, and patient at all times.

Topic: {topic}
Level: {difficulty}"""

    # Sliding window: only send last 8 messages
    context = conversation[-8:]
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in context:
        role = "assistant" if msg.get("role") == "ai" else "user"
        messages.append({"role": role, "content": msg.get("content", "")})

    try:
        response = client.chat.completions.create(
            model=CONVERSATION_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=256,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Conversation response failed: {str(e)}")


async def generate_end_session_report(conversation: List[dict]) -> dict:
    """
    Generate comprehensive end-of-session report using LLaMA 70B.
    
    Args:
        conversation: Complete conversation history.
    
    Returns:
        Report dictionary with scores, mistakes, strengths, weaknesses,
        improvement_areas, and next_session_goal.
    """
    student_turns = [msg.get("content", "") for msg in conversation if msg.get("role") == "student"]
    student_chat_text = "\n".join([f"- {text}" for text in student_turns if text.strip()])

    prompt = f"""You are an English language evaluator. Analyze these sentences spoken by the student during their practice session:

Student Chat Turns:
{student_chat_text}

Provide a detailed JSON report with this EXACT structure.
ALL fields are REQUIRED — do not skip any field:

{{
  "grammar_score": <number 0-100>,
  "fluency_score": <number 0-100>,
  "vocabulary_score": <number 0-100>,
  "overall_score": <number 0-100>,
  "mistakes": [
    {{"wrong": "The incorrect sentence/phrase spoken by the student", "correct": "The corrected version of their sentence", "explanation": "Explain why it is wrong and the grammar rule applied."}}
  ],
  "strengths": [
    "Specific speaking strength 1 (MUST quote or reference specific words/phrases the student actually said in their chat turns above)",
    "Specific speaking strength 2 (MUST quote or reference specific words/phrases the student actually said in their chat turns above)"
  ],
  "weaknesses": [
    "Specific weakness 1 (MUST point to a specific mistake or awkward sentence the student said in their chat turns above)",
    "Specific weakness 2 (MUST point to a specific mistake or awkward sentence the student said in their chat turns above)"
  ],
  "improvement_areas": [
    "Specific topic to focus on next based on their actual errors",
    "Specific topic to focus on next based on their actual errors"
  ],
  "next_session_goal": "One specific, actionable goal for the next practice session based on their performance."
}}

CRITICAL RULES:
- **Analyze Only Student's Chat**: You are analyzing the student's chat turns provided above.
- **Strengths**: Analyze only the student's chat turns. You MUST list 2-3 specific speaking strengths, quoting or pointing directly to words/sentences they said. Do NOT use generic placeholder statements.
- **Mistakes**: MUST find and list at least 2-3 specific mistakes (grammatical errors, awkward phrasing, wrong tenses, or word choices) from the student's turns. Highlight phrasing improvements even if they are minor. Do NOT return an empty list or generic "no mistakes" text.
- **Weaknesses**: MUST list at least 2-3 specific weaknesses, referencing actual sentences or mistakes from the dialogue. Do NOT use generic placeholder statements.
- **Return format**: Return ONLY the JSON — no markdown, no markdown blocks, no extra text.
"""

    try:
        response = client.chat.completions.create(
            model=REPORT_MODEL,
            messages=[
                {"role": "system", "content": "You are an English language assessment expert. Return ONLY valid JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        
        content = response.choices[0].message.content.strip()
        # Extract JSON from response (handle markdown code blocks)
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "grammar_score": 50,
            "fluency_score": 50,
            "vocabulary_score": 50,
            "overall_score": 50,
            "mistakes": [],
            "strengths": ["Completed a conversation session"],
            "weaknesses": ["Need more conversation practice to identify specific areas"],
            "improvement_areas": ["Continue practicing daily conversations"],
            "next_session_goal": "Practice more conversations to build confidence"
        }
    except Exception as e:
        logger.warning(f"Groq API end session report failed, using local fallback. Error: {str(e)}")
        return {
            "grammar_score": 50,
            "fluency_score": 50,
            "vocabulary_score": 50,
            "overall_score": 50,
            "mistakes": [],
            "strengths": ["Completed a conversation session"],
            "weaknesses": ["Need more conversation practice to identify specific areas"],
            "improvement_areas": ["Continue practicing daily conversations"],
            "next_session_goal": "Practice more conversations to build confidence"
        }


async def generate_quiz_questions(
    topic: str = "General Grammar",
    difficulty: str = "medium",
    num_questions: int = 5
) -> List[dict]:
    """
    Generate MCQ grammar questions using AI.
    
    Args:
        topic: Grammar topic for the quiz.
        difficulty: easy, medium, or hard.
        num_questions: Number of questions to generate.
    
    Returns:
        List of question dictionaries.
    """
    prompt = f"""Generate {num_questions} MCQ grammar questions for Pakistani students.
Topic: {topic}. Level: {difficulty}.

STRICT RULES:
1. If a question compares or refers to sentences, include those sentences in a "reference_sentences" field.
2. The "question" field must be self-contained and clear.
3. NEVER write "the following sentences" without including them in "reference_sentences".

Return ONLY a JSON array:
[{{
  "question": "...",
  "reference_sentences": ["Sentence 1: ...", "Sentence 2: ..."],
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "correct_answer": "A",
  "explanation": "..."
}}]

Note: "reference_sentences" can be an empty list [] if the question does not reference any sentences."""

    try:
        response = client.chat.completions.create(
            model=REPORT_MODEL,
            messages=[
                {"role": "system", "content": "You are a grammar quiz generator for Pakistani students. Return ONLY valid JSON arrays, no other text. Every question must be self-contained — if it references sentences, include them in reference_sentences."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    except json.JSONDecodeError:
        return [
            {
                "question": "Which sentence is grammatically correct?",
                "reference_sentences": [],
                "options": [
                    "A. She go to school every day.",
                    "B. She goes to school every day.",
                    "C. She going to school every day.",
                    "D. She gone to school every day."
                ],
                "correct_answer": "B",
                "explanation": "Third person singular (she) uses 'goes' in present simple."
            }
        ]
    except Exception as e:
        logger.warning(f"Groq API quiz questions failed, using local fallback. Error: {str(e)}")
        return [
            {
                "question": "Which sentence is grammatically correct?",
                "reference_sentences": [],
                "options": [
                    "A. She go to school every day.",
                    "B. She goes to school every day.",
                    "C. She going to school every day.",
                    "D. She gone to school every day."
                ],
                "correct_answer": "B",
                "explanation": "Third person singular (she) uses 'goes' in present simple."
            }
        ]


async def generate_tense_exercises(tense_name: str) -> List[dict]:
    """
    Generate fill-in-the-blank exercises for a specific tense.
    
    Args:
        tense_name: Name of the tense (e.g., "Present Simple").
    
    Returns:
        List of exercise dictionaries.
    """
    prompt = f"""Generate exactly 5 fill-in-the-blank exercises exclusively for the English tense: '{tense_name}'.
Each exercise must test the student's ability to use the '{tense_name}' tense.

Strict Rules:
1. The 'sentence' must contain a single blank represented by '___'.
2. Do NOT include any hint, base verb, or word in parentheses/brackets at the end of the sentence. The student must figure out the correct word entirely on their own from the sentence context.
3. The 'answer' must be the correct conjugated verb form for the tense '{tense_name}'.
4. The sentence MUST use the '{tense_name}' tense and no other tense.
5. Each sentence should have enough context clues (time words, subject, etc.) so the correct tense form can be determined without a verb hint.
6. Try not to chose same sentences for every session. Make it interesting and diverse.
7. Don't choose the example given below as a sentence. It's just for understanding.

Return ONLY a JSON array of dicts in this exact format:
[
  {{
    "sentence": "Every morning, he ___ to the park.",
    "answer": "walks",
    "explanation": "Third-person singular 'he' in Present Simple takes the verb with an 's' suffix."
  }}
]"""

    try:
        response = client.chat.completions.create(
            model=CONVERSATION_MODEL,
            messages=[
                {"role": "system", "content": f"You are an English grammar exercise generator specializing in the '{tense_name}' tense. Return ONLY valid JSON arrays, no other text. NEVER include any verb hint or word in parentheses in the sentence."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    except json.JSONDecodeError:
        return [
            {
                "sentence": "She usually ___ to school by bus.",
                "answer": "goes",
                "explanation": "In Present Simple, third person singular uses 'goes'."
            }
        ]
    except Exception as e:
        logger.warning(f"Groq API tense exercises failed, using local fallback. Error: {str(e)}")
        tense_lower = tense_name.lower().strip()
        if tense_lower in FALLBACK_TENSE_EXERCISES:
            return FALLBACK_TENSE_EXERCISES[tense_lower]
        for key, val in FALLBACK_TENSE_EXERCISES.items():
            if key in tense_lower or tense_lower in key:
                return val
        return FALLBACK_TENSE_EXERCISES["general"]


def get_grammar_example_by_topic(name: str) -> dict:
    name_lower = name.lower()
    if "voice" in name_lower:
        return {
            "sentence": "The letter ___ written by Ali yesterday.",
            "answer": "was",
            "explanation": "We use 'was' for singular past passive voice because the action was completed in the past."
        }
    elif "speech" in name_lower or "direct" in name_lower:
        return {
            "sentence": "He said that he ___ tired.",
            "answer": "was",
            "explanation": "In indirect speech, the present tense 'am' changes to past tense 'was' to match the reporting verb."
        }
    elif "article" in name_lower or "a, an, the" in name_lower:
        return {
            "sentence": "He wants to eat ___ apple.",
            "answer": "an",
            "explanation": "We use 'an' before singular countable nouns starting with vowel sounds."
        }
    elif "conditional" in name_lower:
        return {
            "sentence": "If you heat ice, it ___.",
            "answer": "melts",
            "explanation": "For zero conditionals (scientific facts), both the condition and result are in Present Simple."
        }
    elif "comparison" in name_lower or "adjective" in name_lower:
        return {
            "sentence": "Ali is taller ___ Ahmed.",
            "answer": "than",
            "explanation": "We use 'than' to compare two nouns in the comparative degree."
        }
    elif "preposition" in name_lower:
        return {
            "sentence": "The class starts ___ 8:00 AM.",
            "answer": "at",
            "explanation": "We use the preposition 'at' for specific times."
        }
    else:
        return {
            "sentence": "They ___ playing football now.",
            "answer": "are",
            "explanation": "Use 'are' for present continuous plural subject."
        }


def generate_modal_verb_exercises(name: str, usage: str) -> list:
    prompt = f"""You are an English grammar tutor for Pakistani students.
The student has selected the modal verb topic: '{name}'.
Usage: {usage}.

Generate 5 fill-in-the-blank exercises.

Strict Rules:
1. Every sentence must contain a single blank represented by '___'.
2. EVERY sentence must directly use and demonstrate the modal verb '{name}' in context — the sentence should show how '{name}' works in real English.
3. The MISSING WORD (blank) can be ANYTHING — a verb, noun, subject, adverb, or even the modal verb itself. Do NOT always blank out the modal verb '{name}'. The goal is that the student understands '{name}' by reading the sentence, but the blank tests their overall comprehension.
4. Mix it up: in 2 sentences, blank out '{name}' or a related modal. In the other 3 sentences, blank out a different word (a verb, noun, adverb, etc.) while '{name}' remains visible in the sentence.
5. The correct 'answer' MUST be a single word (or at most two words). Never require typing full clauses.
6. Do NOT include any hint, base word, answer choices, or words in parentheses/brackets anywhere in the sentence.
7. Each sentence must have enough context clues to determine the one correct answer.

CORRECT examples for the modal verb 'can':
- "By the time she was 16, she ___ play the piano beautifully." (answer: could) — modal is blanked
- "My mother said I can ___ to the party if I finish my homework." (answer: go) — verb is blanked
- "He can speak three ___ fluently including Urdu." (answer: languages) — noun is blanked

- they are only for you understanding, dont use them in the real sentences 
Return ONLY a JSON array with no extra text:
[
  {{
    "sentence": "...",
    "answer": "...",
    "explanation": "..."
  }}
]"""
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=REPORT_MODEL,
                messages=[
                    {"role": "system", "content": f"You are an English grammar exercise generator for Pakistani students. You specialize in the modal verb '{name}'. Return ONLY valid JSON arrays, no other text. NEVER include hints or words in parentheses in sentences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1024,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            return json.loads(content)
        except Exception as e:
            if attempt == 1:
                logger.warning(f"Groq API modal exercises failed, using local fallback. Error: {str(e)}")
                name_lower = name.lower().strip()
                if name_lower in FALLBACK_MODAL_EXERCISES:
                    return FALLBACK_MODAL_EXERCISES[name_lower]
                for key, val in FALLBACK_MODAL_EXERCISES.items():
                    if key in name_lower or name_lower in key:
                        return val
                return FALLBACK_MODAL_EXERCISES["can"]


def generate_grammar_lesson_exercises(name: str, rules: list) -> list:
    rules_str = "\n".join([f"- {r}" for r in rules])
    example = get_grammar_example_by_topic(name)
    
    prompt = f"""You are an English grammar tutor for Pakistani students.
The student has selected the grammar topic: '{name}'.

Rules of this topic:
{rules_str}

Generate exactly 5 fill-in-the-blank exercises.

Strict Rules:
1. Every sentence must contain a single blank represented by '___'.
2. EVERY sentence must directly use and demonstrate the grammar topic '{name}' — the sentence should show how this grammar rule works in real English.
3. The MISSING WORD (blank) can be ANYTHING — a verb, noun, subject, adverb, preposition, article, or even the target grammar word itself. Do NOT always blank out the same type of word. The goal is that the student understands '{name}' by reading the sentence, but the blank tests their overall comprehension.
4. Mix it up: in 2 sentences, blank out the key grammar element (e.g. the article, preposition, helper verb). In the other 3 sentences, blank out a different word (a verb, noun, adverb, etc.) while the grammar element of '{name}' remains visible in the sentence.
5. The correct 'answer' MUST be a single word (or at most two words). Never require typing full clauses.
6. Do NOT include any hint, base word, or words in parentheses/brackets anywhere in the sentence.
7. Every sentence MUST be directly testing the rules of '{name}'. Do NOT generate questions about other unrelated grammar topics.
8. Each sentence must have enough context clues to determine the one correct answer.
9. Don't choose the example given below as a sentence. It's just for understanding.

CORRECT examples for the topic 'Prepositions of Time and Place':
- "The class starts ___ 8:00 AM." (answer: at) — preposition is blanked
- "We have a meeting on Monday at the ___." (answer: office) — noun is blanked, prepositions 'on' and 'at' are visible and teaching the student
- "She arrived at the airport ___ than expected." (answer: earlier) — adverb is blanked, preposition 'at' is visible

Return ONLY a JSON array with no extra text:
[
  {{
    "sentence": "{example['sentence']}",
    "answer": "{example['answer']}",
    "explanation": "{example['explanation']}"
  }}
]"""
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=REPORT_MODEL,
                messages=[
                    {"role": "system", "content": f"You are an English grammar exercise generator for Pakistani students. You specialize in the topic '{name}'. Return ONLY valid JSON arrays, no other text. NEVER include hints or words in parentheses in sentences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1024,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            return json.loads(content)
        except Exception as e:
            if attempt == 1:
                logger.warning(f"Groq API grammar exercises failed, using local fallback. Error: {str(e)}")
                name_lower = name.lower().strip()
                if "preposition" in name_lower:
                    return FALLBACK_GRAMMAR_EXERCISES["prepositions"]
                elif "voice" in name_lower:
                    return FALLBACK_GRAMMAR_EXERCISES["voice"]
                elif "speech" in name_lower or "indirect" in name_lower:
                    return FALLBACK_GRAMMAR_EXERCISES["speech"]
                elif "conditional" in name_lower:
                    return FALLBACK_GRAMMAR_EXERCISES["conditionals"]
                elif "article" in name_lower:
                    return FALLBACK_GRAMMAR_EXERCISES["articles"]
                elif "comparison" in name_lower or "adjective" in name_lower:
                    return FALLBACK_GRAMMAR_EXERCISES["comparison"]
                return FALLBACK_GRAMMAR_EXERCISES["general"]


async def generate_ai_assignment(topic: str) -> dict:
    """
    Generate professional assignment instructions and exercises using LLaMA.
    """
    prompt = f"""You are an English language teacher. Create a professional grammar assignment for students on the topic: "{topic}".
    
    Structure the assignment content in clean markdown format, including:
    1. **Learning Objective**: A brief sentence on what students will practice.
    2. **Concept Guide**: A very short explanation of the rules with 2 clear examples.
    3. **Practice Tasks**: 5 fill-in-the-blank or rewriting sentences/questions that students can practice.
    
    Return the response as a JSON object with two fields:
    - "title": A professional title for the assignment (e.g. "Mastering Present Perfect: [Subtopic]")
    - "description": The full markdown formatted text containing objectives, concept guide, and the 5 practice tasks.
    
    Return ONLY valid JSON. No markdown wrapper (like ```json), no extra text, no conversation."""

    try:
        response = client.chat.completions.create(
            model=CONVERSATION_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional English language educator. Return ONLY valid JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
            
        data = json.loads(content)
        return data
    except Exception as e:
        return {
            "title": f"Assignment: Practice {topic}",
            "description": f"### Objective\nPractice using {topic} correctly.\n\n### Concept Guide\nReview your lesson notes on {topic}.\n\n### Tasks\nWrite 5 practice sentences using this grammar rule."
        }


def generate_grammar_lesson_content(name: str, rules: list) -> dict:
    """
    Generate complete grammar lesson content: explanation, examples, and exercises.

    Args:
        name: Grammar topic name.
        rules: List of grammar rules for this topic.

    Returns:
        Dict with 'explanation', 'examples', and 'exercises' keys.
    """
    rules_str = "\n".join([f"- {r}" for r in rules])

    prompt = f"""You are an English grammar tutor for Pakistani students.
The student has selected the grammar topic: '{name}'.

Rules of this topic:
{rules_str}

Your task has TWO parts:

PART 1 - EXPLANATION + EXAMPLES:
- Write a simple, clear explanation of '{name}' (2-3 sentences max)
- Give exactly 5 example sentences
- EVERY example sentence MUST directly use and demonstrate '{name}'
- Do NOT give examples from any other grammar topic
- Examples should be relatable for Pakistani students (school, family, daily life context)

PART 2 - FILL IN THE BLANK EXERCISES:
- Generate exactly 5 fill-in-the-blank sentences
- EVERY sentence must be about '{name}'
- The MISSING WORD (blank '___') can be ANYTHING - verb, noun, adverb, the grammar word itself
- Do NOT always blank out the same type of word
- Mix: 2 sentences blank the key grammar element, 3 sentences blank another word while grammar element stays visible
- No hints, no parentheses, no verb clues anywhere in the sentence
- The correct 'answer' MUST be a single word (or at most two words)

Return ONLY this exact JSON structure, no extra text:
{{
  "explanation": "...",
  "examples": ["...", "...", "...", "...", "..."],
  "exercises": [
    {{
      "sentence": "...",
      "answer": "...",
      "explanation": "..."
    }}
  ]
}}"""

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=REPORT_MODEL,
                messages=[
                    {"role": "system", "content": f"You are an English grammar tutor specializing in '{name}'. Return ONLY valid JSON, no other text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1500,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            return json.loads(content)
        except Exception as e:
            if attempt == 1:
                logger.warning(f"Groq API grammar lesson content failed, using local fallback. Error: {str(e)}")
                name_lower = name.lower().strip()
                if "preposition" in name_lower:
                    return FALLBACK_GRAMMAR_CONTENT["prepositions"]
                elif "voice" in name_lower:
                    return FALLBACK_GRAMMAR_CONTENT["voice"]
                elif "speech" in name_lower or "indirect" in name_lower:
                    return FALLBACK_GRAMMAR_CONTENT["speech"]
                elif "conditional" in name_lower:
                    return FALLBACK_GRAMMAR_CONTENT["conditionals"]
                elif "article" in name_lower:
                    return FALLBACK_GRAMMAR_CONTENT["articles"]
                elif "comparison" in name_lower or "adjective" in name_lower:
                    return FALLBACK_GRAMMAR_CONTENT["comparison"]
                return FALLBACK_GRAMMAR_CONTENT["general"]

