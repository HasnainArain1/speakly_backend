-- =========================================
-- SPEAKLY DATABASE SCHEMA — COMPLETE v3
-- FastAPI + PostgreSQL + Supabase Ready
-- Updates:
--   - tenses: added formula + urdu_explanation
--   - vocabulary: added urdu_meaning column
--   - Better seed data for both tables
-- =========================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================
-- ORGANIZATIONS
-- =========================================

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    name VARCHAR(255) NOT NULL,

    plan VARCHAR(20) NOT NULL DEFAULT 'trial'
        CHECK (plan IN ('trial','starter','growth','academy')),

    max_seats INTEGER NOT NULL DEFAULT 50
        CHECK (max_seats > 0),

    seats_used INTEGER NOT NULL DEFAULT 0
        CHECK (seats_used >= 0),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =========================================
-- USERS
-- =========================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    organization_id UUID
        REFERENCES organizations(id)
        ON DELETE SET NULL,

    email VARCHAR(255) UNIQUE NOT NULL,

    password_hash TEXT NOT NULL,

    first_name VARCHAR(100) NOT NULL,

    last_name VARCHAR(100),

    role VARCHAR(20) NOT NULL
        CHECK (
            role IN (
                'super_admin',
                'owner',
                'teacher',
                'student'
            )
        ),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    total_points INTEGER NOT NULL DEFAULT 0,
    current_streak INTEGER NOT NULL DEFAULT 0,

    last_login TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_role ON users(role);

-- =========================================
-- ALLOWED STUDENTS
-- (email whitelist — seat control)
-- =========================================

CREATE TABLE allowed_students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    organization_id UUID NOT NULL
        REFERENCES organizations(id)
        ON DELETE CASCADE,

    email VARCHAR(255) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    added_by UUID
        REFERENCES users(id)
        ON DELETE SET NULL,

    added_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (organization_id, email)
);

CREATE INDEX idx_allowed_org ON allowed_students(organization_id);
CREATE INDEX idx_allowed_email ON allowed_students(email);

-- =========================================
-- TENSES
-- (updated: added formula + urdu_explanation)
-- =========================================

CREATE TABLE tenses (
    id SERIAL PRIMARY KEY,

    name VARCHAR(100) UNIQUE NOT NULL,

    -- sentence structure: "Subject + V1 + s/es"
    formula VARCHAR(200) NOT NULL,

    -- English explanation
    explanation TEXT,

    -- Urdu explanation for Pakistani students
    urdu_explanation TEXT,

    -- single example sentence
    example TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =========================================
-- VOCABULARY
-- (updated: added urdu_meaning column)
-- =========================================

CREATE TABLE vocabulary (
    id SERIAL PRIMARY KEY,

    word VARCHAR(100) UNIQUE NOT NULL,

    -- English meaning/definition
    meaning TEXT NOT NULL,

    -- Urdu meaning — new column
    urdu_meaning VARCHAR(255),

    example_sentence TEXT,

    difficulty VARCHAR(20)
        CHECK (
            difficulty IN (
                'easy',
                'medium',
                'hard'
            )
        ),

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vocab_word ON vocabulary(word);

-- =========================================
-- ASSIGNMENTS
-- =========================================

CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    organization_id UUID NOT NULL
        REFERENCES organizations(id)
        ON DELETE CASCADE,

    teacher_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    title VARCHAR(255) NOT NULL,

    description TEXT,

    max_score INTEGER NOT NULL DEFAULT 100,

    due_date TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_assignments_teacher ON assignments(teacher_id);

-- =========================================
-- ASSIGNMENT SUBMISSIONS
-- =========================================

CREATE TABLE assignment_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    assignment_id UUID NOT NULL
        REFERENCES assignments(id)
        ON DELETE CASCADE,

    student_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    score INTEGER,

    feedback TEXT,

    submitted_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (assignment_id, student_id)
);

-- =========================================
-- VOICE SESSIONS
-- =========================================

CREATE TABLE voice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    student_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    topic VARCHAR(200),

    grammar_score INTEGER
        CHECK (grammar_score BETWEEN 0 AND 100),

    vocabulary_score INTEGER
        CHECK (vocabulary_score BETWEEN 0 AND 100),

    fluency_score INTEGER
        CHECK (fluency_score BETWEEN 0 AND 100),

    overall_score INTEGER
        CHECK (overall_score BETWEEN 0 AND 100),

    duration_seconds INTEGER DEFAULT 0,

    -- full conversation: [{"role":"ai","content":"..."},{"role":"student","content":"..."}]
    conversation JSONB NOT NULL DEFAULT '[]',

    -- AI generated end report: {mistakes:[...], tips:[...], suggestions:[...]}
    report JSONB,

    summary TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_voice_student ON voice_sessions(student_id);

-- =========================================
-- QUIZ SESSIONS
-- =========================================

CREATE TABLE quiz_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    student_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    score INTEGER NOT NULL,

    total_questions INTEGER NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_quiz_student ON quiz_sessions(student_id);

-- =========================================
-- STUDENT TENSE PROGRESS
-- =========================================

CREATE TABLE student_tense_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    student_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    tense_id INTEGER NOT NULL
        REFERENCES tenses(id)
        ON DELETE CASCADE,

    mastery_percent INTEGER NOT NULL DEFAULT 0
        CHECK (mastery_percent BETWEEN 0 AND 100),

    last_practiced_at TIMESTAMP,

    UNIQUE(student_id, tense_id)
);

-- =========================================
-- STUDENT VOCABULARY
-- =========================================

CREATE TABLE student_vocabulary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    student_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    vocabulary_id INTEGER NOT NULL
        REFERENCES vocabulary(id)
        ON DELETE CASCADE,

    learned BOOLEAN NOT NULL DEFAULT FALSE,

    learned_at TIMESTAMP,

    UNIQUE(student_id, vocabulary_id)
);

-- =========================================
-- WORD OF THE DAY
-- =========================================

CREATE TABLE word_of_day (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    vocabulary_id INTEGER NOT NULL
        REFERENCES vocabulary(id)
        ON DELETE CASCADE,

    display_date DATE UNIQUE NOT NULL
);

-- =========================================
-- ACTIVITY LOGS
-- =========================================

CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID
        REFERENCES users(id)
        ON DELETE CASCADE,

    action VARCHAR(255) NOT NULL,

    metadata JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activity_user ON activity_logs(user_id);

-- =========================================
-- UPDATED_AT TRIGGER
-- =========================================

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_org_updated_at
BEFORE UPDATE ON organizations
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_user_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- =========================================
-- SEED TENSES — COMPLETE (12 rows)
-- formula + explanation + urdu + example
-- =========================================

INSERT INTO tenses (name, formula, explanation, urdu_explanation, example) VALUES

('Present Simple',
 'Subject + V1 (s/es for he/she/it)',
 'Used for daily habits, general facts, and routines. The action happens regularly or is always true.',
 'یہ tense روزمرہ کی عادات، حقائق اور معمول کے کاموں کے لیے استعمال ہوتا ہے۔ جیسے کوئی کام ہمیشہ یا اکثر ہوتا ہو۔',
 'I eat rice every day. / She goes to school. / The sun rises in the east.'),

('Present Continuous',
 'Subject + is/am/are + V-ing',
 'Used for actions that are happening right now, at this moment, or around this time.',
 'یہ tense ابھی ہو رہے کاموں کے لیے استعمال ہوتا ہے — جو کام بولتے وقت جاری ہو۔',
 'I am eating lunch right now. / She is studying for her exam. / They are playing cricket.'),

('Present Perfect',
 'Subject + has/have + V3 (past participle)',
 'Used for actions that happened in the past but are connected to or relevant to the present.',
 'یہ tense ماضی کے ان کاموں کے لیے ہے جو مکمل ہو چکے ہیں لیکن ان کا اثر ابھی بھی موجود ہے۔',
 'I have eaten already. / She has gone to Karachi. / They have finished their homework.'),

('Present Perfect Continuous',
 'Subject + has/have been + V-ing',
 'Used for actions that started in the past and are still continuing now, often emphasizing duration.',
 'یہ tense ان کاموں کے لیے ہے جو ماضی میں شروع ہوئے اور ابھی تک جاری ہیں، عموماً وقت کی مدت بتانے کے لیے۔',
 'I have been studying for two hours. / She has been working here since 2020.'),

('Past Simple',
 'Subject + V2 (past form)',
 'Used for actions that were completed at a specific time in the past.',
 'یہ tense ماضی میں مکمل ہونے والے کاموں کے لیے ہے — جو کام ہو چکا اور ختم ہو گیا۔',
 'I ate rice this morning. / She went to school yesterday. / They played cricket last night.'),

('Past Continuous',
 'Subject + was/were + V-ing',
 'Used for actions that were in progress at a specific moment in the past.',
 'یہ tense ماضی میں کسی خاص وقت جاری رہنے والے کاموں کے لیے استعمال ہوتا ہے۔',
 'I was eating when she called. / They were playing when it rained. / She was studying all night.'),

('Past Perfect',
 'Subject + had + V3 (past participle)',
 'Used for an action that was completed BEFORE another action in the past. The earlier action uses Past Perfect.',
 'جب ماضی میں دو کام ہوئے ہوں تو جو کام پہلے ہوا اس کے لیے Past Perfect اور بعد والے کے لیے Past Simple استعمال ہوتا ہے۔',
 'I had eaten before she arrived. / The train had left when we reached the station.'),

('Past Perfect Continuous',
 'Subject + had been + V-ing',
 'Used for an action that was ongoing for a period of time before another past action happened.',
 'یہ tense ماضی کے ایک کام سے پہلے کسی اور کام کے جاری رہنے کی مدت بتانے کے لیے استعمال ہوتا ہے۔',
 'I had been waiting for an hour when she finally arrived. / He had been working all day before he got sick.'),

('Future Simple',
 'Subject + will + V1 (base form)',
 'Used for decisions made at the moment of speaking, predictions, and promises about the future.',
 'یہ tense مستقبل کے کاموں، فیصلوں، وعدوں اور پیشین گوئیوں کے لیے استعمال ہوتا ہے۔',
 'I will eat later. / She will go to Lahore tomorrow. / I think it will rain today.'),

('Future Continuous',
 'Subject + will be + V-ing',
 'Used for actions that will be in progress at a specific moment in the future.',
 'یہ tense مستقبل میں کسی خاص وقت جاری رہنے والے کام کے لیے استعمال ہوتا ہے۔',
 'At 8pm tonight I will be eating dinner. / This time tomorrow she will be flying to Dubai.'),

('Future Perfect',
 'Subject + will have + V3 (past participle)',
 'Used for actions that will be completed before a specific time in the future.',
 'یہ tense مستقبل میں کسی مقررہ وقت سے پہلے مکمل ہونے والے کاموں کے لیے استعمال ہوتا ہے۔',
 'I will have finished my homework by 9pm. / She will have left before you arrive.'),

('Future Perfect Continuous',
 'Subject + will have been + V-ing',
 'Used for actions that will have been ongoing for a period of time up to a specific future moment.',
 'یہ tense مستقبل میں کسی وقت تک کسی کام کے جاری رہنے کی مدت بتانے کے لیے استعمال ہوتا ہے۔',
 'By December I will have been studying English for two years. / She will have been working here for 5 years next month.');


-- =========================================
-- SEED VOCABULARY — 40 words with Urdu
-- Add full Oxford 3000 list later
-- =========================================

INSERT INTO vocabulary (word, meaning, urdu_meaning, example_sentence, difficulty) VALUES

-- easy words
('achieve',       'to successfully reach a desired goal or result',           'حاصل کرنا',           'Work hard to achieve your dreams.',                    'easy'),
('afraid',        'feeling fear or worry about something',                    'ڈرا ہوا، خوف زدہ',    'She was afraid of speaking in public.',                'easy'),
('angry',         'feeling strong displeasure or annoyance',                  'غصے میں',              'He got angry when he lost the game.',                  'easy'),
('beautiful',     'pleasing to the senses, especially sight',                 'خوبصورت',              'The flowers are very beautiful.',                      'easy'),
('brave',         'having courage and not being afraid of danger',            'بہادر',                'The soldier was very brave.',                          'easy'),
('busy',          'having a lot of things to do, not free',                   'مصروف',                'I am very busy today with my work.',                   'easy'),
('careful',       'paying attention to avoid mistakes or danger',             'محتاط',                'Be careful when crossing the road.',                   'easy'),
('clever',        'quick to understand and learn things',                     'ہوشیار، ذہین',         'She is a very clever student.',                        'easy'),
('confident',     'feeling certain about your own abilities',                 'پر اعتماد',            'He answered the question confidently.',                'easy'),
('daily',         'happening every day',                                      'روزانہ',               'Exercise is part of my daily routine.',                'easy'),
('earn',          'to get money by working',                                  'کمانا',                'He earns money by teaching English.',                  'easy'),
('explain',       'to make something clear or easy to understand',            'سمجھانا',              'Please explain the rule again.',                       'easy'),
('famous',        'known by many people',                                     'مشہور',                'Quaid-e-Azam is a famous leader of Pakistan.',         'easy'),
('friendly',      'behaving in a kind and pleasant way',                      'دوستانہ، ملنسار',      'Our new teacher is very friendly.',                    'easy'),
('honest',        'not lying or cheating, truthful',                         'ایماندار',             'Always be honest with your parents.',                  'easy'),
('improve',       'to become or make something better',                       'بہتر کرنا',            'Practice daily to improve your English.',              'easy'),
('lazy',          'not willing to work or use effort',                        'سست',                  'Do not be lazy — study every day.',                    'easy'),
('mistake',       'something done incorrectly, an error',                     'غلطی',                 'Everyone makes mistakes while learning.',              'easy'),
('nervous',       'feeling worried or anxious',                               'گھبراہٹ میں',          'She felt nervous before the exam.',                    'easy'),
('polite',        'having good manners and showing respect',                  'شائستہ، تمیزدار',      'Always be polite when speaking to elders.',            'easy'),

-- medium words
('ambition',      'a strong desire to achieve something',                     'عزم، خواہش',           'His ambition is to become a doctor.',                  'medium'),
('communicate',   'to share information or express feelings',                 'بات چیت کرنا',         'It is important to communicate clearly.',              'medium'),
('concentrate',   'to focus your attention on something',                     'توجہ مرکوز کرنا',      'Concentrate on your studies to pass.',                 'medium'),
('consequence',   'a result or effect of an action',                          'نتیجہ، انجام',         'Think about the consequences before deciding.',        'medium'),
('creative',      'having the ability to make new ideas or things',           'تخلیقی',               'She is a very creative writer.',                       'medium'),
('curious',       'eager to know or learn about something',                   'متجسس',                'Children are naturally curious about the world.',      'medium'),
('determine',     'to decide firmly or find out exactly',                     'طے کرنا، پکا ارادہ',   'She determined to pass her exam no matter what.',     'medium'),
('diligent',      'showing care and effort in your work',                     'محنتی، مستعد',         'Diligent students always succeed in life.',            'medium'),
('fluent',        'able to speak a language smoothly and easily',             'روانی سے بولنے والا',  'She is fluent in three languages.',                    'medium'),
('grateful',      'feeling thankful for something received',                  'شکر گزار',             'I am grateful for your help.',                         'medium'),
('influence',     'the power to affect how someone thinks or acts',           'اثر، اثر و رسوخ',      'Teachers have a great influence on students.',         'medium'),
('opportunity',   'a chance to do something good or useful',                  'موقع',                 'Education gives you the opportunity to grow.',         'medium'),
('patient',       'able to wait calmly without getting angry',                'صبر والا',             'Be patient — learning takes time.',                    'medium'),
('persuade',      'to convince someone to do or believe something',           'قائل کرنا',            'He tried to persuade his friend to study.',            'medium'),
('responsible',   'having a duty to deal with something',                     'ذمہ دار',              'A good student is responsible for their work.',        'medium'),

-- hard words
('articulate',    'able to express ideas clearly and effectively',            'واضح طور پر بیان کرنا','She is very articulate in her presentations.',         'hard'),
('eloquent',      'fluent and persuasive in speaking or writing',             'بلیغ، فصیح',           'The speaker gave an eloquent speech.',                 'hard'),
('persevere',     'to continue doing something despite difficulty',           'ثابت قدم رہنا',         'You must persevere even when things get hard.',        'hard'),
('profound',      'very great, deep, or intense',                             'گہرا، اثر انگیز',       'Reading has a profound effect on vocabulary.',         'hard'),
('sophisticated', 'having refined knowledge and understanding',               'پیچیدہ، باریک بین',     'Her writing style is very sophisticated.',             'hard');


-- =========================================
-- DONE — SPEAKLY SCHEMA v3
-- 14 tables total
-- tenses: 12 rows with formula + Urdu
-- vocabulary: 40 words with Urdu meanings
-- =========================================
