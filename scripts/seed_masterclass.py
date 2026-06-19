"""
Seed script to populate modal_verbs and grammar_lessons tables.
"""

from app.database import SessionLocal
from app.models import ModalVerb, GrammarLesson

MODAL_VERBS_DATA = [
    {
        "name": "can",
        "usage": "Expresses ability, permission, or request in the present.",
        "urdu_explanation": "کسی کام کو کرنے کی صلاحیت یا اجازت ظاہر کرتا ہے۔ (سکتا ہے، سکتی ہے، سکتے ہیں)",
        "positive_form": "Subject + can + Verb (1st form)",
        "negative_form": "Subject + cannot (can't) + Verb (1st form)",
        "question_form": "Can + Subject + Verb (1st form)?",
        "examples": ["I can speak English.", "Can I borrow your pen?", "You cannot swim here."],
        "order_index": 1
    },
    {
        "name": "could",
        "usage": "Expresses past ability, polite request, or possibility.",
        "urdu_explanation": "ماضی کی صلاحیت یا انتہائی شائستہ درخواست ظاہر کرتا ہے۔ (سکا، سکی، سکتے تھے)",
        "positive_form": "Subject + could + Verb (1st form)",
        "negative_form": "Subject + could not (couldn't) + Verb (1st form)",
        "question_form": "Could + Subject + Verb (1st form)?",
        "examples": ["He could run fast when he was young.", "Could you pass the salt, please?", "It could rain tonight."],
        "order_index": 2
    },
    {
        "name": "may",
        "usage": "Expresses formal permission, possibility, or wish.",
        "urdu_explanation": "رسمی اجازت، امکان یا دعا دینے کے لیے استعمال ہوتا ہے۔ (شاید، ہو سکتا ہے)",
        "positive_form": "Subject + may + Verb (1st form)",
        "negative_form": "Subject + may not + Verb (1st form)",
        "question_form": "May + Subject + Verb (1st form)?",
        "examples": ["May I come in, teacher?", "She may arrive late.", "May Allah bless you!"],
        "order_index": 3
    },
    {
        "name": "might",
        "usage": "Expresses a weak or past possibility.",
        "urdu_explanation": "بہت کم یا ماضی کے امکان کو ظاہر کرنے کے لیے۔ (شاید ہی ایسا ہو)",
        "positive_form": "Subject + might + Verb (1st form)",
        "negative_form": "Subject + might not + Verb (1st form)",
        "question_form": "Might + Subject + Verb (1st form)?",
        "examples": ["They might join us if they finish early.", "He might not like this idea.", "Might I ask a question?"],
        "order_index": 4
    },
    {
        "name": "must",
        "usage": "Expresses strong necessity, obligation, or logical certainty.",
        "urdu_explanation": "کسی کام کی لازمی ضرورت، فرض یا یقینی ہونے کو ظاہر کرتا ہے۔ (ضرور چاہیے، لازمی ہے)",
        "positive_form": "Subject + must + Verb (1st form)",
        "negative_form": "Subject + must not (mustn't) + Verb (1st form)",
        "question_form": "Must + Subject + Verb (1st form)?",
        "examples": ["You must wear a helmet.", "She must be tired after the long walk.", "We mustn't tell anyone."],
        "order_index": 5
    },
    {
        "name": "shall",
        "usage": "Used for offers, suggestions, or future tense with I/We.",
        "urdu_explanation": "تجاویز، پیشکش یا مستقبل کی بات کے لیے استعمال ہوتا ہے۔ (گا، گی، گے)",
        "positive_form": "Subject + shall + Verb (1st form)",
        "negative_form": "Subject + shall not (shan't) + Verb (1st form)",
        "question_form": "Shall + Subject + Verb (1st form)?",
        "examples": ["Shall we dance?", "I shall meet you tomorrow.", "We shall not give up."],
        "order_index": 6
    },
    {
        "name": "should",
        "usage": "Used to give advice, opinion, or recommendation.",
        "urdu_explanation": "نصیحت، رائے یا سفارش ظاہر کرتا ہے۔ (چاہیے)",
        "positive_form": "Subject + should + Verb (1st form)",
        "negative_form": "Subject + should not (shouldn't) + Verb (1st form)",
        "question_form": "Should + Subject + Verb (1st form)?",
        "examples": ["You should eat healthy food.", "Should I call him now?", "We shouldn't waste time."],
        "order_index": 7
    },
    {
        "name": "will",
        "usage": "Expresses future certainty, determination, or promise.",
        "urdu_explanation": "مستقبل کے یقین، عزم یا وعدے کو ظاہر کرتا ہے۔ (گا، گی، گے)",
        "positive_form": "Subject + will + Verb (1st form)",
        "negative_form": "Subject + will not (won't) + Verb (1st form)",
        "question_form": "Will + Subject + Verb (1st form)?",
        "examples": ["I will help you.", "They won't come to the party.", "Will she call us?"],
        "order_index": 8
    },
    {
        "name": "would",
        "usage": "Used for polite requests, preferences, conditional statements, or past habits.",
        "urdu_explanation": "شائستہ درخواست، ماضی کی عادت، یا خیالی بات کے لیے۔ (کرتا تھا، پسند کرے گا)",
        "positive_form": "Subject + would + Verb (1st form)",
        "negative_form": "Subject + would not (wouldn't) + Verb (1st form)",
        "question_form": "Would + Subject + Verb (1st form)?",
        "examples": ["Would you like some tea?", "If I were rich, I would travel.", "He would play cricket every Sunday."],
        "order_index": 9
    }
]

GRAMMAR_LESSONS_DATA = [
    {
        "category": "voice",
        "name": "Active and Passive Voice",
        "urdu_explanation": "فعلیہ اور مفعولہ جملے جن میں سبجیکٹ یا ابجیکٹ کی اہمیت بدلی جاتی ہے۔",
        "rules": [
            "In Passive Voice, the object of the active sentence becomes the subject.",
            "Use the auxiliary verb 'to be' in the correct tense followed by Past Participle (3rd form).",
            "Use 'by' before the agent who does the action."
        ],
        "examples": [
            "Active: Ali wrote a letter. -> Passive: A letter was written by Ali.",
            "Active: She cleans the room. -> Passive: The room is cleaned by her."
        ],
        "order_index": 1
    },
    {
        "category": "speech",
        "name": "Direct and Indirect Speech",
        "urdu_explanation": "کسی کی کہی ہوئی بات کو جوں کا توں دہرانا یا اپنے الفاظ میں بیان کرنا۔",
        "rules": [
            "Remove quotation marks for indirect speech.",
            "Change tenses: Present Simple -> Past Simple, Present Continuous -> Past Continuous.",
            "Change pronouns according to the speaker."
        ],
        "examples": [
            "Direct: He said, 'I am tired.' -> Indirect: He said that he was tired.",
            "Direct: She says, 'I will write.' -> Indirect: She says that she will write."
        ],
        "order_index": 2
    },
    {
        "category": "articles",
        "name": "Definite and Indefinite Articles (A, An, The)",
        "urdu_explanation": "حروف تخصیص جو کسی چیز کے مخصوص ہونے یا عام ہونے کو بتاتے ہیں۔",
        "rules": [
            "Use 'a' before singular countable nouns with consonant sounds.",
            "Use 'an' before singular countable nouns with vowel sounds.",
            "Use 'the' for specific or unique nouns."
        ],
        "examples": [
            "I saw an elephant yesterday.",
            "Please hand me the blue pen.",
            "He is a teacher at Apex coaching center."
        ],
        "order_index": 3
    },
    {
        "category": "conditionals",
        "name": "Zero Conditional",
        "urdu_explanation": "عام سچائی یا سائنسی حقائق کے متعلق جملے جہاں نتیجہ ہمیشہ یقینی ہوتا ہے۔",
        "rules": [
            "Structure: If/When + Present Simple, Present Simple.",
            "Used for facts, habits, and absolute truths."
        ],
        "examples": [
            "If you heat ice, it melts.",
            "If you get water on paper, it gets wet."
        ],
        "order_index": 4
    },
    {
        "category": "conditionals",
        "name": "First Conditional",
        "urdu_explanation": "مستقبل کے ممکنہ حالات اور ان کے متوقع نتائج کے جملے۔",
        "rules": [
            "Structure: If + Present Simple, Will + Verb (1st form).",
            "Refers to real and possible future conditions."
        ],
        "examples": [
            "If it rains, we will stay at home.",
            "If you study hard, you will pass the exam."
        ],
        "order_index": 5
    },
    {
        "category": "conditionals",
        "name": "Second Conditional",
        "urdu_explanation": "غیر حقیقی، خیالی یا غیر ممکنہ موجودہ/مستقبل کے حالات کے جملے۔",
        "rules": [
            "Structure: If + Past Simple, Would + Verb (1st form).",
            "Used for imaginary or highly unlikely situations."
        ],
        "examples": [
            "If I won the lottery, I would buy a big house.",
            "If I were you, I would consult a doctor."
        ],
        "order_index": 6
    },
    {
        "category": "conditionals",
        "name": "Third Conditional",
        "urdu_explanation": "ماضی کے غیر حقیقی حالات اور ان کے ماضی میں ہی ممکنہ نتائج (پچھتاوے) کے جملے۔",
        "rules": [
            "Structure: If + Past Perfect, Would have + Verb (3rd form).",
            "Used to express regret or imaginary past actions."
        ],
        "examples": [
            "If I had studied harder, I would have passed the exam.",
            "If she had woken up early, she wouldn't have missed the bus."
        ],
        "order_index": 7
    },
    {
        "category": "comparison",
        "name": "Degrees of Adjectives Comparison",
        "urdu_explanation": "صفت کے درجے جو دو یا دو سے زیادہ چیزوں کے مابین موازنے کے لیے استعمال ہوتے ہیں۔",
        "rules": [
            "Positive Degree: base adjective (e.g., tall, beautiful).",
            "Comparative Degree: compare two nouns (e.g., taller, more beautiful). Add 'than'.",
            "Superlative Degree: compare three or more nouns (e.g., tallest, most beautiful). Use 'the'."
        ],
        "examples": [
            "Ali is taller than Ahmed.",
            "Mt. Everest is the tallest mountain in the world.",
            "She is more creative than her sister."
        ],
        "order_index": 8
    },
    {
        "category": "prepositions",
        "name": "Prepositions of Time and Place",
        "urdu_explanation": "وقت اور جگہ کو جملے میں ظاہر کرنے والے الفاظ۔ (ان، ایٹ، آن)",
        "rules": [
            "Use 'at' for specific times, exact locations, and addresses.",
            "Use 'in' for months, years, centuries, and enclosed spaces.",
            "Use 'on' for days, dates, and flat surfaces."
        ],
        "examples": [
            "The class starts at 8:00 AM.",
            "The book is on the table.",
            "We were born in the 21st century."
        ],
        "order_index": 9
    }
]


def seed():
    db = SessionLocal()
    try:
        print("Starting seed of modal_verbs and grammar_lessons...")

        # Seed Modal Verbs by matching name
        for item in MODAL_VERBS_DATA:
            existing = db.query(ModalVerb).filter(ModalVerb.name == item["name"]).first()
            if not existing:
                verb = ModalVerb(**item)
                db.add(verb)
                print(f"Added Modal Verb: {item['name']}")
            else:
                # Update attributes
                for key, val in item.items():
                    setattr(existing, key, val)
                print(f"Updated Modal Verb: {item['name']}")

        # Seed Grammar Lessons by matching name
        for item in GRAMMAR_LESSONS_DATA:
            existing = db.query(GrammarLesson).filter(GrammarLesson.name == item["name"]).first()
            if not existing:
                lesson = GrammarLesson(**item)
                db.add(lesson)
                print(f"Added Grammar Lesson: {item['name']}")
            else:
                # Update attributes
                for key, val in item.items():
                    setattr(existing, key, val)
                print(f"Updated Grammar Lesson: {item['name']}")

        db.commit()
        print("Database seeded successfully!")

    except Exception as e:
        db.rollback()
        # Clean print of exception to avoid CP1252 encoding error
        print(f"Error during seeding: {type(e).__name__} - check server logs")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
