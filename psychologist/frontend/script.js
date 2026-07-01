// ZARA — Offline AI Emotional Support Assistant
document.addEventListener('DOMContentLoaded', () => {
    // ===== STATE =====
    let currentView = 'assistant'; // 'assistant' | 'voice' | 'advanced'
    let currentLanguage = localStorage.getItem('cognitiveMindLanguage') || 'en';
    let companionSessionActive = false;
    let companionSessionId = null;
    let voiceState = 'idle'; // 'idle' | 'listening' | 'pause_analysis' | 'thinking' | 'speaking' | 'error'
    let selectedInputType = 'Observation';
    let inputHistory = JSON.parse(localStorage.getItem('cognitiveMindHistory') || '[]');
    let currentFilter = 'all';
    let step = 0;

    // ===== i18n TRANSLATIONS =====
    const translations = {
        en: {
            "app_name": "ZARA",
            "badge_offline_text": "Offline Secured",
            "btn_voice_mode": "Voice Mode",
            "btn_advanced": "Advanced Mind View",
            "btn_back_assistant": "Back to Chat",
            "language_toggle_bangla": "বাংলা",
            "language_toggle_english": "English",
            "chip_talk": "Talk to Zara",
            "chip_help_think": "Help me think",
            "chip_explain_mood": "Explain my mood",
            "mood_how_feeling": "How are you feeling?",
            "mood_great": "Great", "mood_okay": "Okay", "mood_low": "Low", "mood_anxious": "Anxious", "mood_angry": "Angry",
            "welcome_text": "Hi, I'm Zara — your offline emotional support companion. How can I help you today?",
            "welcome_sub": "Type a message or tap the mic to speak.",
            "chat_placeholder": "Message Zara...",
            "btn_send": "Send",
            "toggle_speak_response": "Read aloud",
            "toggle_push_to_talk": "Push-to-Talk",
            "voice_idle": "Tap the mic and speak to Zara",
            "voice_listening": "I'm listening...",
            "voice_processing": "Thinking locally...",
            "voice_speaking": "Zara is speaking...",
            "voice_error": "Microphone unavailable. Please check permission.",
            "voice_take_your_time": "Take your time.",
            "voice_thinking": "Thinking locally...",
            "voice_interrupted": "Interrupted. I'm listening.",
            "voice_settings": "Voice Settings",
            "voice_speed": "Speech Speed",
            "voice_volume": "Volume",
            "voice_continuous": "Continuous Listening",
            "voice_playback_speed": "Playback Speed",
            "live_transcript_header": "Live Transcript:",
            "nav_dashboard": "Dashboard", "nav_emotions": "Emotions", "nav_needs": "Needs",
            "nav_beliefs": "Beliefs", "nav_goals": "Goals", "nav_conflicts": "Inner Conflicts",
            "nav_identity": "Self-Identity", "nav_memory": "Memory", "nav_graph": "Knowledge Graph",
            "nav_debate": "Internal Debate", "nav_simulation": "Future Preview", "nav_history": "Input History",
            "nav_thoughts": "Zara's Thinking",
            "title_dashboard": "Cognitive State Overview", "title_emotions": "Emotion State",
            "title_needs": "Internal Needs", "title_beliefs": "Belief System",
            "title_goals": "Goals", "title_conflicts": "Inner Conflicts",
            "title_identity": "Self-Identity", "title_memory": "Memory Timeline",
            "title_graph": "Knowledge Graph", "title_debate": "Internal Debate",
            "title_simulation": "Future Preview", "title_history": "Input History",
            "card_header_cognitive_state": "COGNITIVE STATE", "card_header_active_emotional": "EMOTIONAL STATE",
            "card_header_dominant_goal": "DOMINANT GOAL", "card_header_system_metrics": "SYSTEM METRICS",
            "sub_exploring": "Adapting to new data", "sub_priority_high": "Priority: HIGH",
            "metric_confidence": "CONFIDENCE", "metric_stability": "STABILITY", "metric_energy": "ENERGY",
            "filter_all": "All", "filter_strong": "Strong", "filter_weak": "Weak",
            "filter_conflicted": "Conflicted", "filter_new": "New",
            "identity_self_confidence": "SELF-CONFIDENCE", "identity_self_consistency": "SELF-CONSISTENCY",
            "identity_knowledge_gaps": "KNOWLEDGE GAPS", "identity_decision_quality": "DECISION QUALITY",
            "identity_emotional_balance": "EMOTIONAL BALANCE", "identity_value_stability": "VALUE STABILITY",
            "sim_scenario_header": "Possible Future Outcome", "sim_risk_score": "Risk",
            "sim_reward_score": "Reward", "sim_consequence_header": "Emotional Consequence",
            "sim_action_header": "Recommended Action",
            "history_search_placeholder": "Search...", "history_filter_all": "All Types",
            "type_observation": "Observation", "type_emotion": "Emotion", "type_memory": "Memory",
            "type_belief": "Belief", "type_goal": "Goal", "type_question": "Question",
            "type_experience": "Experience",
            "console_classification_label": "Input Type:",
            "console_input_placeholder": "Send to Zara...",
            "console_submit_button": "Send to Zara",
            "slider_happiness": "Happy", "slider_sadness": "Sad", "slider_fear": "Fear",
            "slider_anger": "Anger", "slider_curiosity": "Curious", "slider_trust": "Trust",
            "slider_motivation": "Motivation", "slider_stress": "Stress",
            "tool_calm_title": "Calm me down", "tool_journal_title": "Start journal",
            "tool_breathing_title": "Breathing Exercise",
            "breathing_breathe_in": "Breathe In...", "breathing_breathe_out": "Breathe Out...",
            "breathing_instruction": "Follow the circle. Breathe in as it expands, breathe out as it contracts.",
            "journal_placeholder": "Write your thoughts here...",
            "journal_save": "Save Entry",
            "safety_banner": "If you're in crisis, please reach out to a local professional helpline. Zara is an offline support tool, not a replacement for professional help.",
            "session_welcome_bn": "হ্যালো, আমি ঝারা। আমি সম্পূর্ণ অফলাইনে আছি। আজ আপনাকে কীভাবে সাহায্য করতে পারি?",
            "session_welcome_en": "Hello, I'm Zara. I'm fully offline and here to listen. How can I help you today?",
            "mood_response_great": "That's wonderful to hear! What's been making you feel great?",
            "mood_response_okay": "Okay is perfectly fine. Is there anything on your mind you'd like to talk about?",
            "mood_response_low": "I'm sorry you're feeling low. I'm here for you. Want to talk about what's bothering you?",
            "mood_response_anxious": "I understand anxiety can be overwhelming. Let's take it one step at a time. Would you like to try a breathing exercise?",
            "mood_response_angry": "It's okay to feel angry. Want to talk about what's frustrating you? Sometimes putting it into words helps.",
            "thought_observation": "Analyzing emotional input...",
            "thought_memory_recall": "Searching memory for patterns...",
            "thought_prediction": "Simulating possible outcomes...",
            "thought_emotional_state": "Monitoring emotional balance...",
            "thought_context_analysis": "Processing context...",
            "thought_self_reflection": "Reflecting on identity...",
            "status_processing": "Processing", "status_thinking": "Thinking",
            "status_analyzing": "Analyzing", "status_learning": "Learning",
            "accuracy_title": "System Accuracy", "accuracy_overall": "Overall Accuracy",
            "accuracy_stt": "Speech Recognition", "accuracy_intent": "Intent Detection",
            "accuracy_safety": "Safety Detection", "accuracy_tool": "Tool Routing",
            "accuracy_response": "Response Quality",
            "accuracy_run_tests": "Run Tests",
            "accuracy_recent_failures": "Recent Failures",
            "accuracy_suggestions": "Suggestions",
        },
        bn_bd: {
            "app_name": "ঝারা",
            "badge_offline_text": "অফলাইন সুরক্ষিত",
            "btn_voice_mode": "ভয়েস মোড",
            "btn_advanced": "অ্যাডভান্সড মাইন্ড ভিউ",
            "btn_back_assistant": "চ্যাটে ফিরুন",
            "language_toggle_bangla": "বাংলা",
            "language_toggle_english": "English",
            "chip_talk": "ঝারার সাথে কথা বলুন",
            "chip_help_think": "চিন্তা করতে সাহায্য করুন",
            "chip_explain_mood": "আমার মেজাজ ব্যাখ্যা করুন",
            "mood_how_feeling": "আপনি কেমন বোধ করছেন?",
            "mood_great": "দারুণ", "mood_okay": "ঠিক আছে", "mood_low": "খারাপ", "mood_anxious": "উদ্বিগ্ন", "mood_angry": "রাগান্বিত",
            "welcome_text": "হ্যালো, আমি ঝারা — আপনার অফলাইন আবেগীয় সহায়তা সহচর। আজ আপনাকে কীভাবে সাহায্য করতে পারি?",
            "welcome_sub": "বার্তা টাইপ করুন বা কথা বলতে মাইক ট্যাপ করুন।",
            "chat_placeholder": "ঝারা কে বার্তা পাঠান...",
            "btn_send": "পাঠান",
            "toggle_speak_response": "উচ্চস্বরে পড়ুন",
            "toggle_push_to_talk": "পুশ-টু-টক",
            "voice_idle": "মাইক ট্যাপ করে ঝারার সাথে কথা বলুন",
            "voice_listening": "আমি শুনছি...",
            "voice_processing": "স্থানীয়ভাবে চিন্তা করছি...",
            "voice_speaking": "ঝারা বলছে...",
            "voice_error": "মাইক্রোফোন পাওয়া যাচ্ছে না। অনুগ্রহ করে অনুমতি পরীক্ষা করুন।",
            "voice_take_your_time": "ধীরে নিন।",
            "voice_thinking": "স্থানীয়ভাবে চিন্তা করছি...",
            "voice_interrupted": "বাধা দেওয়া হয়েছে। আমি শুনছি।",
            "voice_settings": "ভয়েস সেটিংস",
            "voice_speed": "কথার গতি",
            "voice_volume": "ভলিউম",
            "voice_continuous": "ক্রমাগত শ্রবণ",
            "voice_playback_speed": "প্লেব্যাক গতি",
            "live_transcript_header": "লাইভ প্রতিলিপি:",
            "nav_dashboard": "ড্যাশবোর্ড", "nav_emotions": "আবেগ", "nav_needs": "প্রয়োজন",
            "nav_beliefs": "বিশ্বাস", "nav_goals": "লক্ষ্য", "nav_conflicts": "অভ্যন্তরীণ দ্বন্দ্ব",
            "nav_identity": "আত্ম-পরিচয়", "nav_memory": "স্মৃতি", "nav_graph": "জ্ঞান গ্রাফ",
            "nav_debate": "অভ্যন্তরীণ বিতর্ক", "nav_simulation": "ভবিষ্যৎ প্রিভিউ", "nav_history": "ইনপুট ইতিহাস",
            "nav_thoughts": "ঝারার চিন্তা",
            "title_dashboard": "জ্ঞানীয় অবস্থা", "title_emotions": "আবেগের অবস্থা",
            "title_needs": "অন্তর্নিহিত প্রয়োজনীয়তা", "title_beliefs": "বিশ্বাস ব্যবস্থা",
            "title_goals": "লক্ষ্য", "title_conflicts": "অভ্যন্তরীণ দ্বন্দ্ব",
            "title_identity": "আত্ম-পরিচয়", "title_memory": "স্মৃতি টাইমলাইন",
            "title_graph": "জ্ঞান গ্রাফ", "title_debate": "অভ্যন্তরীণ বিতর্ক",
            "title_simulation": "ভবিষ্যৎ প্রিভিউ", "title_history": "ইনপুট ইতিহাস",
            "card_header_cognitive_state": "জ্ঞানীয় অবস্থা", "card_header_active_emotional": "আবেগের অবস্থা",
            "card_header_dominant_goal": "প্রধান লক্ষ্য", "card_header_system_metrics": "সিস্টেম মেট্রিক্স",
            "sub_exploring": "নতুন ডেটার সাথে খাপ খাইয়ে নিচ্ছে", "sub_priority_high": "অগ্রাধিকার: উচ্চ",
            "metric_confidence": "আত্মবিশ্বাস", "metric_stability": "স্থিতিশীলতা", "metric_energy": "শক্তি",
            "filter_all": "সব", "filter_strong": "শক্তিশালী", "filter_weak": "দুর্বল",
            "filter_conflicted": "দ্বন্দ্বিত", "filter_new": "নতুন",
            "identity_self_confidence": "আত্মবিশ্বাস", "identity_self_consistency": "আত্ম-সামঞ্জস্য",
            "identity_knowledge_gaps": "জ্ঞানের ফাঁক", "identity_decision_quality": "সিদ্ধান্তের গুণমান",
            "identity_emotional_balance": "আবেগের ভারসাম্য", "identity_value_stability": "মূল্যের স্থিতিশীলতা",
            "sim_scenario_header": "সম্ভাব্য ভবিষ্যৎ ফলাফল", "sim_risk_score": "ঝুঁকি",
            "sim_reward_score": "পুরস্কার", "sim_consequence_header": "আবেগের পরিণতি",
            "sim_action_header": "সুপারিশকৃত পদক্ষেপ",
            "history_search_placeholder": "সার্চ...", "history_filter_all": "সব ধরন",
            "type_observation": "পর্যবেক্ষণ", "type_emotion": "আবেগ", "type_memory": "স্মৃতি",
            "type_belief": "বিশ্বাস", "type_goal": "লক্ষ্য", "type_question": "প্রশ্ন",
            "type_experience": "অভিজ্ঞতা",
            "console_classification_label": "ইনপুটের ধরন:",
            "console_input_placeholder": "ঝারা কে পাঠান...",
            "console_submit_button": "ঝারা কে পাঠান",
            "slider_happiness": "সুখ", "slider_sadness": "দুঃখ", "slider_fear": "ভয়",
            "slider_anger": "রাগ", "slider_curiosity": "কৌতূহল", "slider_trust": "বিশ্বাস",
            "slider_motivation": "উদ্দীপনা", "slider_stress": "চাপ",
            "tool_calm_title": "আমাকে শান্ত করুন", "tool_journal_title": "জার্নাল শুরু করুন",
            "tool_breathing_title": "শ্বাস-প্রশ্বাসের ব্যায়াম",
            "breathing_breathe_in": "শ্বাস নিন...", "breathing_breathe_out": "শ্বাস ছাড়ুন...",
            "breathing_instruction": "বৃত্তটি অনুসরণ করুন। প্রসারিত হলে শ্বাস নিন, সংকুচিত হলে শ্বাস ছাড়ুন।",
            "journal_placeholder": "আপনার চিন্তা এখানে লিখুন...",
            "journal_save": "এন্ট্রি সংরক্ষণ করুন",
            "safety_banner": "আপনি যদি সংকটে থাকেন, অনুগ্রহ করে স্থানীয় পেশাদার হেলপলাইনে যোগাযোগ করুন। ঝারা একটি অফলাইন সহায়তা টুল, পেশাদার সাহায্যের বিকল্প নয়।",
            "session_welcome_bn": "হ্যালো, আমি ঝারা। আমি সম্পূর্ণ অফলাইনে আছি। আজ আপনাকে কীভাবে সাহায্য করতে পারি?",
            "session_welcome_en": "Hello, I'm Zara. I'm fully offline and here to listen. How can I help you today?",
            "mood_response_great": "এটা শুনতে দারুণ! কী আপনাকে এত ভালো অনুভব করাচ্ছে?",
            "mood_response_okay": "ঠিক আছে থাকাটা পুরোপুরি স্বাভাবিক। আপনার মনে কিছু আছে কি যে নিয়ে কথা বলতে চান?",
            "mood_response_low": "আপনি খারাপ অনুভব করছেন শুনে দুঃখিত। আমি আপনার পাশে আছি। কী নিয়ে চিন্তিত তা নিয়ে কথা বলতে চান?",
            "mood_response_anxious": "আমি বুঝতে পারি উদ্বেগ কতটা কঠিন হতে পারে। এক এক করে এগোই। শ্বাস-প্রশ্বাসের ব্যায়াম চেষ্টা করতে চান?",
            "mood_response_angry": "রাগান্বিত অনুভব করাটা স্বাভাবিক। কী আপনাকে বিরক্ত করছে তা নিয়ে কথা বলতে চান? কখনও কখনও কথা বললে হালকা লাগে।",
            "thought_observation": "আবেগিক ইনপুট বিশ্লেষণ করা হচ্ছে...",
            "thought_memory_recall": "প্যাটার্নের জন্য স্মৃতি অনুসন্ধান করা হচ্ছে...",
            "thought_prediction": "সম্ভাব্য ফলাফল সিমুলেট করা হচ্ছে...",
            "thought_emotional_state": "আবেগের ভারসাম্য পর্যবেক্ষণ করা হচ্ছে...",
            "thought_context_analysis": "প্রসঙ্গ প্রক্রিয়াকরণ করা হচ্ছে...",
            "thought_self_reflection": "পরিচয় নিয়ে প্রতিচ্ছবি করা হচ্ছে...",
            "status_processing": "\u09aa\u09cd\u09b0\u0995\u09cd\u09b0\u09bf\u09af\u09bc\u09be\u0995\u09b0\u09a3", "status_thinking": "\u099a\u09bf\u09a8\u09cd\u09a4\u09be \u0995\u09b0\u099b\u09c7",
            "status_analyzing": "\u09ac\u09bf\u09b6\u09cd\u09b2\u09c7\u09b7\u09a3 \u0995\u09b0\u099b\u09c7", "status_learning": "\u09b6\u09bf\u0996\u099b\u09c7",
            "accuracy_title": "\u09b8\u09bf\u09b8\u09cd\u099f\u09c7\u09ae \u09a8\u09bf\u09b0\u09cd\u0997\u09c1\u09b2\u09a4\u09be", "accuracy_overall": "\u09b8\u09be\u09ae\u0997\u09cd\u09b0\u09bf\u0995 \u09a8\u09bf\u09b0\u09cd\u0997\u09c1\u09b2\u09a4\u09be",
            "accuracy_stt": "\u09ac\u09be\u0995 \u09b6\u09cd\u09b0\u09c1\u09a4\u09bf\u099a\u09df\u09a8", "accuracy_intent": "\u0989\u09a6\u09cd\u09a6\u09c7\u09b6\u09cd\u09af \u09b6\u09a8\u09be\u0995\u09cd\u09a4\u0995\u09b0\u09a3",
            "accuracy_safety": "\u09a8\u09bf\u09b0\u09be\u09aa\u09a4\u09cd\u09a4\u09be \u09b6\u09a8\u09be\u0995\u09cd\u09a4\u0995\u09b0\u09a3", "accuracy_tool": "\u099f\u09c1\u09b2 \u09b0\u09be\u0989\u099f\u09bf\u0982",
            "accuracy_response": "\u0989\u09a4\u09cd\u09a4\u09b0\u09c7\u09b0 \u09ae\u09be\u09a8",
            "accuracy_run_tests": "\u09aa\u09b0\u09c0\u0995\u09cd\u09b7\u09be \u099a\u09be\u09b2\u09be\u09a8",
            "accuracy_recent_failures": "\u09b8\u09be\u09ae\u09cd\u09aa\u09cd\u09b0\u09a4\u09bf\u0995 \u09ac\u09cd\u09af\u09b0\u09cd\u09a5\u09a4\u09be",
            "accuracy_suggestions": "\u09aa\u09b0\u09be\u09ae\u09b0\u09cd\u09b6",
        }
    };

    function t(key) { return (translations[currentLanguage] || translations.en)[key] || key; }

    function applyTranslations(lang) {
        const tr = translations[lang] || translations.en;
        document.querySelectorAll('[data-i18n]').forEach(el => { const k = el.getAttribute('data-i18n'); if (tr[k]) el.textContent = tr[k]; });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { const k = el.getAttribute('data-i18n-placeholder'); if (tr[k]) el.placeholder = tr[k]; });
        document.querySelectorAll('[data-i18n-title]').forEach(el => { const k = el.getAttribute('data-i18n-title'); if (tr[k]) el.title = tr[k]; });
        document.documentElement.lang = lang === 'bn_bd' ? 'bn' : 'en';
        const langToggle = document.getElementById('languageToggle');
        if (langToggle) { langToggle.textContent = lang === 'en' ? tr.language_toggle_bangla : tr.language_toggle_english; }
        localStorage.setItem('cognitiveMindLanguage', lang);
        currentLanguage = lang;
    }
    applyTranslations(currentLanguage);

    // ===== VIEW SWITCHING =====
    const assistantView = document.getElementById('assistantView');
    const voiceView = document.getElementById('voiceView');
    const advancedView = document.getElementById('advancedView');

    function showView(name) {
        assistantView.classList.remove('active');
        advancedView.classList.remove('active');
        voiceView.classList.remove('active');
        currentView = name;
        if (name === 'assistant') assistantView.classList.add('active');
        else if (name === 'voice') voiceView.classList.add('active');
        else if (name === 'advanced') advancedView.classList.add('active');
    }

    document.getElementById('voiceModeBtn').addEventListener('click', () => { showView('voice'); });
    // voiceCloseBtn handler is in the Voice Mode section (with conversation cleanup)
    document.getElementById('advancedViewBtn').addEventListener('click', () => { showView('advanced'); });
    document.getElementById('backToAssistantBtn').addEventListener('click', () => { showView('assistant'); });

    // ===== ASSISTANT MODE: CHAT =====
    const chatArea = document.getElementById('chatArea');
    const chatInput = document.getElementById('chatInput');
    const chatSendBtn = document.getElementById('chatSendBtn');
    const chatMicBtn = document.getElementById('chatMicBtn');
    const speakResponseToggle = document.getElementById('speakResponseToggle');
    const chatWelcome = document.getElementById('chatWelcome');

    function appendMessage(sender, text, emotion) {
        if (chatWelcome) chatWelcome.style.display = 'none';
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${sender}`;
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = text;
        msgDiv.appendChild(bubble);
        const meta = document.createElement('div');
        meta.className = 'message-meta';
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        meta.innerHTML = `<span>${timeStr}</span>`;
        if (emotion) meta.innerHTML += ` <span class="emotion-tag">${emotion}</span>`;
        msgDiv.appendChild(meta);
        // Action buttons for assistant messages
        if (sender === 'assistant') {
            const actions = document.createElement('div');
            actions.className = 'msg-actions';
            actions.innerHTML = `<button class="msg-action-btn" onclick="navigator.clipboard.writeText(this.closest('.chat-message').querySelector('.message-bubble').textContent)">Copy</button>`;
            msgDiv.appendChild(actions);
        }
        chatArea.appendChild(msgDiv);
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        chatArea.appendChild(indicator);
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function removeTypingIndicator() {
        const el = document.getElementById('typingIndicator');
        if (el) el.remove();
    }

    async function sendChatMessage(text) {
        if (!text) return;
        chatInput.value = '';
        appendMessage('user', text);
        showTypingIndicator();
        // Ensure session is active
        if (!companionSessionActive) {
            try {
                const res = await fetch('/api/session/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: 'text', language: currentLanguage }) });
                const data = await res.json();
                if (data.session_id) { companionSessionId = data.session_id; companionSessionActive = true; }
            } catch (e) { console.error('Session start error:', e); }
        }
        try {
            const res = await fetch('/api/interaction/message', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, language: currentLanguage, speak_response: speakResponseToggle.checked })
            });
            const result = await res.json();
            removeTypingIndicator();
            if (result.assistant_message) {
                appendMessage('assistant', result.assistant_message.response_text, result.assistant_message.response_type);
            } else if (result.response) {
                appendMessage('assistant', result.response, result.dominant_emotion);
            } else {
                appendMessage('assistant', currentLanguage === 'bn_bd' ? 'দুঃখিত, আমি এখন সাহায্য করতে পারছি না।' : 'I\'m sorry, I\'m having trouble responding right now.');
            }
        } catch (e) {
            removeTypingIndicator();
            console.error('Chat error:', e);
            appendMessage('assistant', currentLanguage === 'bn_bd' ? 'সংযোগ ত্রুটি। অনুগ্রহ করে আবার চেষ্টা করুন।' : 'Connection error. Please try again.');
        }
    }

    chatSendBtn.addEventListener('click', () => sendChatMessage(chatInput.value.trim()));
    chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(chatInput.value.trim()); } });
    // Auto-resize textarea
    chatInput.addEventListener('input', () => { chatInput.style.height = 'auto'; chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px'; });

    // ===== MOOD SELECTOR =====
    document.querySelectorAll('.mood-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            const mood = btn.dataset.mood;
            const responseKey = `mood_response_${mood}`;
            appendMessage('user', currentLanguage === 'bn_bd' ? `আমি ${btn.querySelector('[data-i18n]').textContent} বোধ করছি` : `I'm feeling ${mood}`);
            setTimeout(() => appendMessage('assistant', t(responseKey)), 500);
        });
    });

    // ===== QUICK ACTION CHIPS =====
    document.querySelectorAll('.chip-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const action = btn.dataset.action;
            if (action === 'talk') { chatInput.focus(); return; }
            if (action === 'calm') {
                try {
                    const res = await fetch('/api/support/calm', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ language: currentLanguage }) });
                    const data = await res.json();
                    appendMessage('assistant', data.content || data.prompt || (currentLanguage === 'bn_bd' ? 'শান্ত হন। গভীর শ্বাস নিন।' : 'Let\'s calm down. Take a deep breath.'));
                } catch (e) { appendMessage('assistant', currentLanguage === 'bn_bd' ? 'শান্ত হন। আপনি নিরাপদ।' : 'Calm down. You are safe.'); }
                return;
            }
            if (action === 'help-think') {
                try {
                    const res = await fetch('/api/support/reflection', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ language: currentLanguage }) });
                    const data = await res.json();
                    appendMessage('assistant', data.questions ? data.questions.join('\n') : (data.content || 'What\'s on your mind?'));
                } catch (e) { appendMessage('assistant', 'What\'s on your mind? Let\'s think through it together.'); }
                return;
            }
            if (action === 'journal') { document.getElementById('journalModal').style.display = 'flex'; return; }
            if (action === 'mood') {
                try {
                    const res = await fetch('/api/support/mood-checkin', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ language: currentLanguage }) });
                    const data = await res.json();
                    appendMessage('assistant', data.content || data.prompt || (data.questions ? data.questions.join('\n') : 'How are you feeling right now?'));
                } catch (e) { appendMessage('assistant', 'Let\'s check in — how are you feeling right now?'); }
                return;
            }
        });
    });

    // ===== VOICE MODE (Conversation Engine) =====
    const voiceOrb = document.getElementById('voiceOrb');
    const voiceStateText = document.getElementById('voiceStateText');
    const voiceTranscript = document.getElementById('voiceTranscript');
    const voiceTranscriptText = document.getElementById('voiceTranscriptText');
    const voiceMeter = document.getElementById('voiceMeter');
    const voiceMeterFill = document.getElementById('voiceMeterFill');
    const voiceMainBtn = document.getElementById('voiceMainBtn');
    const voiceMuteBtn = document.getElementById('voiceMuteBtn');
    const voiceInterruptBtn = document.getElementById('voiceInterruptBtn');
    const voiceResponseText = document.getElementById('voiceResponseText');
    // New controls
    const voiceSpeedControls = document.getElementById('voiceSpeedControls');
    const voiceVolumeSlider = document.getElementById('voiceVolumeSlider');
    const voiceSettingsToggle = document.getElementById('voiceSettingsToggle');
    const voiceSettingsPanel = document.getElementById('voiceSettingsPanel');

    let voiceEventSource = null;
    let conversationActive = false;
    let lastUserTranscript = '';

    function setVoiceState(state) {
        voiceState = state;
        voiceView.setAttribute('data-state', state);
        // Map backend states to display keys
        const stateKeyMap = {
            'idle': 'voice_idle', 'listening': 'voice_listening',
            'pause_analysis': 'voice_listening', 'thinking': 'voice_processing',
            'speaking': 'voice_speaking', 'error': 'voice_error'
        };
        voiceStateText.textContent = t(stateKeyMap[state] || 'voice_idle');
        voiceMainBtn.classList.toggle('recording', state === 'listening' || state === 'pause_analysis');
        voiceTranscript.style.display = ['listening', 'pause_analysis', 'thinking'].includes(state) ? 'block' : 'none';
        voiceMeter.style.display = ['listening', 'pause_analysis'].includes(state) ? 'block' : 'none';
        voiceSpeedControls.style.display = state === 'speaking' ? 'flex' : 'none';
        voiceResponseText.style.display = state === 'speaking' ? 'block' : 'none';
    }

    function openSSEStream() {
        if (voiceEventSource) { voiceEventSource.close(); }
        voiceEventSource = new EventSource('/api/voice/conversation/events');

        voiceEventSource.addEventListener('state_change', (e) => {
            try {
                const data = JSON.parse(e.data);
                setVoiceState(data.state);
                if (data.message) voiceStateText.textContent = data.message;
            } catch (err) { console.warn('SSE state_parse error:', err); }
        });

        voiceEventSource.addEventListener('partial_transcript', (e) => {
            try {
                const data = JSON.parse(e.data);
                voiceTranscriptText.textContent = data.text || '';
                if (data.text) lastUserTranscript = data.text;
            } catch (err) { console.warn('SSE transcript_parse error:', err); }
        });

        voiceEventSource.addEventListener('audio_level', (e) => {
            try {
                const data = JSON.parse(e.data);
                voiceMeterFill.style.width = Math.min(100, Math.round((data.level || 0) * 1000)) + '%';
            } catch (err) { /* ignore */ }
        });

        voiceEventSource.addEventListener('response', (e) => {
            try {
                const data = JSON.parse(e.data);
                voiceResponseText.style.display = 'block';
                voiceResponseText.textContent = data.text || '';
                // Add to chat history
                if (lastUserTranscript) appendMessage('user', lastUserTranscript);
                if (data.text) appendMessage('assistant', data.text, data.emotion);
                lastUserTranscript = '';
            } catch (err) { console.warn('SSE response_parse error:', err); }
        });

        voiceEventSource.addEventListener('playback_state', (e) => {
            try {
                const data = JSON.parse(e.data);
                if (data.progress !== undefined) {
                    // Could update a progress bar here in future
                }
            } catch (err) { /* ignore */ }
        });

        voiceEventSource.addEventListener('error', (e) => {
            try {
                const data = JSON.parse(e.data);
                setVoiceState('error');
                voiceStateText.textContent = data.message || t('voice_error');
            } catch (err) {
                // SSE connection error (not a data event)
                console.warn('SSE connection error, reconnecting...');
            }
        });

        voiceEventSource.onerror = () => {
            // EventSource will auto-reconnect; if conversation ended, clean up
            if (!conversationActive && voiceEventSource) {
                voiceEventSource.close();
                voiceEventSource = null;
            }
        };
    }

    function closeSSEStream() {
        if (voiceEventSource) { voiceEventSource.close(); voiceEventSource = null; }
    }

    // Main voice button: start/stop conversation
    voiceMainBtn.addEventListener('click', async () => {
        if (voiceState === 'idle' || voiceState === 'error') {
            // Start conversation
            try {
                const res = await fetch('/api/voice/conversation/start', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ language: currentLanguage })
                });
                const data = await res.json();
                if (data.status === 'started' || data.status === 'listening') {
                    conversationActive = true;
                    openSSEStream();
                    setVoiceState('listening');
                    voiceTranscriptText.textContent = t('voice_listening');
                } else if (data.error) {
                    setVoiceState('error');
                    voiceStateText.textContent = data.error;
                }
            } catch (e) {
                console.error('Voice conversation start error:', e);
                setVoiceState('error');
            }
        } else if (voiceState === 'listening' || voiceState === 'pause_analysis') {
            // Stop conversation
            conversationActive = false;
            try { await fetch('/api/voice/conversation/stop', { method: 'POST' }); } catch (e) {}
            closeSSEStream();
            voiceMeterFill.style.width = '0%';
            setVoiceState('idle');
            voiceTranscriptText.textContent = '';
            voiceResponseText.style.display = 'none';
        }
    });

    // Interrupt button: stop TTS, return to listening
    voiceInterruptBtn.addEventListener('click', async () => {
        try {
            await fetch('/api/voice/conversation/interrupt', { method: 'POST' });
        } catch (e) { /* ignore */ }
        try { await fetch('/api/voice/tts/pause', { method: 'POST' }); } catch (e) {}
        voiceStateText.textContent = t('voice_interrupted') || 'Interrupted. I\'m listening.';
    });

    // Mute toggle
    let isMuted = false;
    voiceMuteBtn.addEventListener('click', () => {
        isMuted = !isMuted;
        speakResponseToggle.checked = !isMuted;
        voiceMuteBtn.style.color = isMuted ? 'var(--neon-red)' : '';
    });

    // Playback speed controls
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const speed = parseFloat(btn.dataset.speed);
            try {
                await fetch('/api/voice/preferences', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ speech_speed: speed })
                });
            } catch (e) { /* ignore */ }
        });
    });

    // Volume slider
    if (voiceVolumeSlider) {
        voiceVolumeSlider.addEventListener('input', async () => {
            const vol = parseInt(voiceVolumeSlider.value) / 100;
            try {
                await fetch('/api/voice/preferences', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ volume: vol })
                });
            } catch (e) { /* ignore */ }
        });
    }

    // Settings panel toggle
    if (voiceSettingsToggle) {
        voiceSettingsToggle.addEventListener('click', () => {
            const panel = voiceSettingsPanel;
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        });
    }

    // Settings toggles (continuous listening, push-to-talk, barge-in)
    document.querySelectorAll('.voice-setting-toggle').forEach(toggle => {
        toggle.addEventListener('change', async () => {
            const key = toggle.dataset.setting;
            const val = toggle.checked;
            try {
                await fetch('/api/voice/preferences', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ [key]: val })
                });
            } catch (e) { /* ignore */ }
        });
    });

    // Clean up voice conversation when leaving voice view
    document.getElementById('voiceCloseBtn').addEventListener('click', async () => {
        if (conversationActive) {
            conversationActive = false;
            try { await fetch('/api/voice/conversation/stop', { method: 'POST' }); } catch (e) {}
            closeSSEStream();
        }
        showView('assistant');
    });

    // Chat mic button -> enter voice mode and start conversation
    chatMicBtn.addEventListener('click', () => { showView('voice'); });

    // ===== BREATHING MODAL =====
    const breathingModal = document.getElementById('breathingModal');
    document.getElementById('breathingClose').addEventListener('click', () => { breathingModal.style.display = 'none'; });
    breathingModal.addEventListener('click', (e) => { if (e.target === breathingModal) breathingModal.style.display = 'none'; });

    // ===== JOURNAL MODAL =====
    const journalModal = document.getElementById('journalModal');
    document.getElementById('journalClose').addEventListener('click', () => { journalModal.style.display = 'none'; });
    journalModal.addEventListener('click', (e) => { if (e.target === journalModal) journalModal.style.display = 'none'; });
    document.getElementById('saveJournalBtn').addEventListener('click', () => {
        const text = document.getElementById('journalTextarea').value;
        if (text) { appendMessage('assistant', currentLanguage === 'bn_bd' ? 'আপনার জার্নাল এন্ট্রি সংরক্ষণ করা হয়েছে।' : 'Your journal entry has been saved.'); }
        document.getElementById('journalTextarea').value = '';
        journalModal.style.display = 'none';
    });

    // ===== SAFETY BANNER =====
    document.getElementById('safetyDismiss').addEventListener('click', () => { document.getElementById('safetyBanner').style.display = 'none'; });

    // ===== EMOTION SLIDERS =====
    document.querySelectorAll('.emotion-slider').forEach(slider => {
        slider.addEventListener('input', (e) => {
            const valEl = document.getElementById(`${e.target.id}Val`);
            if (valEl) valEl.textContent = e.target.value;
        });
    });

    // ===== PILLS (Input Type) =====
    document.querySelectorAll('.pill-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedInputType = btn.dataset.type;
        });
    });

    // ===== COGNITIVE SUBMIT (Advanced) =====
    document.getElementById('cognitiveSubmitBtn').addEventListener('click', async () => {
        const input = document.getElementById('cognitiveInput');
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        const additionalEmotions = {};
        document.querySelectorAll('.emotion-slider').forEach(s => {
            additionalEmotions[s.id.replace('slider', '').toLowerCase()] = parseInt(s.value) / 100;
        });
        try {
            const res = await fetch('/api/emotion/process', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, additionalEmotions })
            });
            const result = await res.json();
            if (result.dominant_emotion) {
                document.getElementById('dominantEmotion').textContent = result.dominant_emotion.toUpperCase();
            }
        } catch (e) { console.error('Cognitive submit error:', e); }
        // Save to history
        inputHistory.unshift({ id: crypto.randomUUID(), text, type: selectedInputType, impact: Math.floor(Math.random() * 60) + 20, time: new Date().toLocaleTimeString() });
        localStorage.setItem('cognitiveMindHistory', JSON.stringify(inputHistory));
        renderHistory();
    });

    // ===== ADVANCED MIND VIEW: NAV =====
    document.querySelectorAll('.adv-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.adv-nav-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.adv-section').forEach(s => s.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.section).classList.add('active');
            if (btn.dataset.section === 'adv-graph') setTimeout(drawKnowledgeGraph, 100);
        });
    });

    // ===== BELIEF FILTERS =====
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderBeliefs();
        });
    });

    // ===== HISTORY =====
    const historySearch = document.getElementById('historySearch');
    const historyFilter = document.getElementById('historyFilter');
    historySearch.addEventListener('input', renderHistory);
    historyFilter.addEventListener('change', renderHistory);
    window.deleteHistoryItem = (id) => {
        inputHistory = inputHistory.filter(item => item.id !== id);
        localStorage.setItem('cognitiveMindHistory', JSON.stringify(inputHistory));
        renderHistory();
    };

    // ===== INITIAL DATA =====
    let initialEmotions = { curiosity: 78, fear: 23, confidence: 85, doubt: 15, motivation: 70, stress: 35, trust: 60, frustration: 18 };
    let initialNeeds = { knowledge: 45, security: 92, exploration: 85, social: 65, achievement: 55, stabilityNeed: 75, autonomy: 88 };
    let beliefs = [
        { id: 1, name: "Social interactions build trust", confidence: 0.88, evidence: 12, contradictions: 1, lastUpdated: "2 min ago", isNew: true },
        { id: 2, name: "Exploration leads to knowledge", confidence: 0.95, evidence: 24, contradictions: 0, lastUpdated: "5 min ago", isNew: false },
        { id: 3, name: "Uncertainty causes stress", confidence: 0.70, evidence: 8, contradictions: 3, lastUpdated: "10 min ago", isNew: false },
        { id: 4, name: "Achievement boosts confidence", confidence: 0.90, evidence: 18, contradictions: 0, lastUpdated: "1 min ago", isNew: true },
        { id: 5, name: "Change is inevitable", confidence: 0.65, evidence: 6, contradictions: 2, lastUpdated: "8 min ago", isNew: false }
    ];
    let goals = [
        { id: 1, title: "Explore unknown territories", priority: "HIGH", sourceNeed: "Exploration", emotionalInfluence: "Curiosity", status: "Active" },
        { id: 2, title: "Build social connections", priority: "MEDIUM", sourceNeed: "Social", emotionalInfluence: "Trust", status: "Active" },
        { id: 3, title: "Consolidate knowledge base", priority: "MEDIUM", sourceNeed: "Knowledge", emotionalInfluence: "Confidence", status: "Paused" },
        { id: 4, title: "Complete previous task", priority: "LOW", sourceNeed: "Achievement", emotionalInfluence: "Pride", status: "Completed" },
        { id: 5, title: "Take unnecessary risk", priority: "LOW", sourceNeed: "Exploration", emotionalInfluence: "Fear", status: "Abandoned" }
    ];
    const conflicts = [
        { left: "Curiosity", right: "Fear", leftPercent: 55, rightPercent: 45 },
        { left: "Safety", right: "Exploration", leftPercent: 40, rightPercent: 60 },
        { left: "Confidence", right: "Doubt", leftPercent: 70, rightPercent: 30 },
        { left: "Logic", right: "Emotion", leftPercent: 45, rightPercent: 55 }
    ];
    const identityMetrics = { confidence: 85, consistency: 78, knowledgeGaps: 23, decisionQuality: 81, emotionalBalance: 69, valueStability: 74 };
    let memoryEvents = [
        { type: "Emotional Shift", content: "Curiosity rose to 78%", time: "0:02" },
        { type: "Goal Updated", content: "Added goal: Explore territories", time: "0:45" },
        { type: "Belief Change", content: "Confidence in social trust increased", time: "1:12" },
        { type: "Important Event", content: "New interaction detected", time: "1:58" },
        { type: "Identity Change", content: "Self-consistency score updated", time: "2:30" },
        { type: "Emotional Shift", content: "Stress reduced to 35%", time: "2:45" }
    ];
    let influenceValues = { emotions: 65, goals: 45, identity: 35, beliefs: 50, memory: 40 };

    // ===== RENDER FUNCTIONS =====
    function renderEmotionBars() {
        const grid = document.getElementById('emotionGrid');
        if (!grid) return;
        const emotionColors = {
            curiosity: 'linear-gradient(90deg, var(--neon-cyan), var(--neon-blue))',
            fear: 'linear-gradient(90deg, var(--neon-orange), var(--neon-red))',
            confidence: 'linear-gradient(90deg, var(--neon-green), #00d070)',
            doubt: 'linear-gradient(90deg, var(--neon-orange), #cc7000)',
            motivation: 'linear-gradient(90deg, var(--neon-purple), #7c3aed)',
            stress: 'linear-gradient(90deg, #ff6b6b, var(--neon-red))',
            trust: 'linear-gradient(90deg, #3b82f6, var(--neon-blue))',
            frustration: 'linear-gradient(90deg, #f59e0b, var(--neon-orange))'
        };
        grid.innerHTML = Object.entries(initialEmotions).map(([key, val]) => `
            <div class="emotion-item">
                <div class="emotion-label"><span>${key.toUpperCase()}</span><span class="emotion-percent">${val}</span></div>
                <div class="emotion-bar"><div class="emotion-fill" style="width:${val}%;background:${emotionColors[key] || 'var(--neon-cyan)'}"></div></div>
            </div>
        `).join('');
    }

    function renderNeeds() {
        const grid = document.getElementById('needsGrid');
        if (!grid) return;
        const needColors = {
            knowledge: 'linear-gradient(90deg, #10b981, var(--neon-green))',
            security: 'linear-gradient(90deg, var(--neon-orange), var(--neon-red))',
            exploration: 'linear-gradient(90deg, var(--neon-cyan), var(--neon-blue))',
            social: 'linear-gradient(90deg, #3b82f6, var(--neon-blue))',
            achievement: 'linear-gradient(90deg, var(--neon-green), #00d070)',
            stabilityNeed: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
            autonomy: 'linear-gradient(90deg, var(--neon-purple), #7c3aed)'
        };
        grid.innerHTML = Object.entries(initialNeeds).map(([key, val]) => `
            <div class="need-item">
                <div class="need-header"><span>${key.toUpperCase().replace('NEED','')}</span><span class="need-percent">${val}</span></div>
                <div class="need-bar"><div class="need-fill" style="width:${val}%;background:${needColors[key] || 'var(--neon-cyan)'}"></div></div>
            </div>
        `).join('');
    }

    function renderBeliefs() {
        const el = document.getElementById('beliefList');
        if (!el) return;
        let filtered = beliefs;
        if (currentFilter === 'strong') filtered = beliefs.filter(b => b.confidence >= 0.8);
        else if (currentFilter === 'weak') filtered = beliefs.filter(b => b.confidence < 0.7);
        else if (currentFilter === 'conflicted') filtered = beliefs.filter(b => b.contradictions > 0);
        else if (currentFilter === 'new') filtered = beliefs.filter(b => b.isNew);
        el.innerHTML = filtered.map(b => `
            <div class="belief-item"><div class="belief-top"><div class="belief-name">${b.name}</div><div class="belief-confidence">${Math.round(b.confidence*100)}%</div></div>
            <div class="belief-meta"><div>Evidence: ${b.evidence}</div><div>Contradictions: ${b.contradictions}</div><div>Updated: ${b.lastUpdated}</div>
            ${b.isNew ? '<span class="badge badge-new">NEW</span>' : ''}${b.contradictions > 0 ? '<span class="badge badge-conflicted">CONFLICTED</span>' : ''}</div></div>
        `).join('');
    }

    function renderGoals() {
        const el = document.getElementById('goalsGrid');
        if (!el) return;
        el.innerHTML = goals.map(g => `
            <div class="goal-card ${g.status.toLowerCase()}"><div class="goal-title">${g.title}</div>
            <div class="goal-meta"><span>Priority: ${g.priority}</span><span>Source: ${g.sourceNeed}</span><span>Emotion: ${g.emotionalInfluence}</span>
            <span class="status-tag status-${g.status.toLowerCase()}">${g.status}</span></div></div>
        `).join('');
    }

    function renderConflicts() {
        const el = document.getElementById('conflictGrid');
        if (!el) return;
        el.innerHTML = conflicts.map(c => `
            <div class="conflict-item"><div class="conflict-title">${c.left} vs ${c.right}</div>
            <div class="conflict-bar"><div class="conflict-left" style="width:${c.leftPercent}%">${c.left} ${c.leftPercent}%</div>
            <div class="conflict-right" style="width:${c.rightPercent}%">${c.right} ${c.rightPercent}%</div></div></div>
        `).join('');
    }

    function renderMemoryTimeline() {
        const el = document.getElementById('memoryTimeline');
        if (!el) return;
        el.innerHTML = memoryEvents.map(e => `
            <div class="memory-item"><div class="memory-time">${e.time}</div><div class="memory-type">${e.type}</div><div class="memory-content">${e.content}</div></div>
        `).join('');
    }

    function renderHistory() {
        const el = document.getElementById('historyList');
        if (!el) return;
        let filtered = inputHistory;
        const search = historySearch.value.toLowerCase();
        if (search) filtered = filtered.filter(i => i.text.toLowerCase().includes(search));
        const ft = historyFilter.value;
        if (ft !== 'all') filtered = filtered.filter(i => i.type === ft);
        el.innerHTML = filtered.map(i => `
            <div class="history-item"><div class="history-content"><div class="history-text">${i.text}</div>
            <div class="history-meta"><span class="history-type">${i.type}</span><span>Impact: ${i.impact}%</span><span>${i.time}</span></div></div>
            <button class="history-delete" onclick="deleteHistoryItem('${i.id}')">×</button></div>
        `).join('');
    }

    function drawKnowledgeGraph() {
        const canvas = document.getElementById('knowledgeGraph');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth; canvas.height = canvas.offsetHeight;
        const w = canvas.width, h = canvas.height;
        ctx.clearRect(0, 0, w, h);
        const nodes = [
            { x: w/2, y: h/3, label: 'SELF', radius: 40, color: '#00f0ff' },
            { x: w/4, y: h/2, label: 'BELIEFS', radius: 30, color: '#00ff88' },
            { x: 3*w/4, y: h/2, label: 'GOALS', radius: 30, color: '#a855f7' },
            { x: w/3, y: 2*h/3, label: 'VALUES', radius: 25, color: '#0066ff' },
            { x: 2*w/3, y: 2*h/3, label: 'EMOTIONS', radius: 32, color: '#ff3366' },
            { x: w/5, y: h/1.5, label: 'MEMORIES', radius: 28, color: '#ff9500' }
        ];
        const edges = [[0,1],[0,2],[0,4],[1,3],[1,5],[2,3],[2,4],[3,4],[4,5]];
        edges.forEach(([a,b]) => { ctx.beginPath(); ctx.strokeStyle='rgba(0,240,255,0.3)'; ctx.lineWidth=2; ctx.moveTo(nodes[a].x,nodes[a].y); ctx.lineTo(nodes[b].x,nodes[b].y); ctx.stroke(); });
        nodes.forEach(n => {
            ctx.shadowBlur=20; ctx.shadowColor=n.color; ctx.beginPath(); ctx.arc(n.x,n.y,n.radius,0,Math.PI*2); ctx.fillStyle=`${n.color}20`; ctx.fill();
            ctx.beginPath(); ctx.arc(n.x,n.y,n.radius,0,Math.PI*2); ctx.strokeStyle=n.color; ctx.lineWidth=2; ctx.stroke();
            ctx.shadowBlur=0; ctx.fillStyle='#e0e0e0'; ctx.font='bold 12px Segoe UI'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(n.label,n.x,n.y);
        });
    }

    // ===== THOUGHT STREAM =====
    function startThoughtStream() {
        const el = document.getElementById('thoughtStream');
        if (!el) return;
        const templates = [
            { label: 'thought_observation', content: 'Analyzing emotional significance of input...' },
            { label: 'thought_memory_recall', content: 'Comparing with past experiences...' },
            { label: 'thought_prediction', content: 'Simulating future outcomes...' },
            { label: 'thought_emotional_state', content: 'Monitoring current emotional state...' },
            { label: 'thought_context_analysis', content: 'Processing context...' },
            { label: 'thought_self_reflection', content: 'Reflecting on identity...' }
        ];
        const addThought = () => {
            const tmpl = templates[Math.floor(Math.random() * templates.length)];
            const timeStr = new Date().toLocaleTimeString([], { hour12: false });
            const item = document.createElement('div');
            item.className = 'thought-item';
            item.innerHTML = `<div class="thought-time">${timeStr}</div><strong>${t(tmpl.label)}:</strong> ${tmpl.content}`;
            el.prepend(item);
            if (el.children.length > 15) el.removeChild(el.lastChild);
        };
        addThought();
        setInterval(addThought, 4000);
    }

    // ===== INIT =====
    renderEmotionBars();
    renderNeeds();
    renderBeliefs();
    renderGoals();
    renderConflicts();
    renderMemoryTimeline();
    renderHistory();
    startThoughtStream();
    showView('assistant');

    // Auto-init session
    (async function initSession() {
        try {
            const res = await fetch('/api/session/current');
            const data = await res.json();
            if (data && data.session_id) {
                companionSessionId = data.session_id;
                companionSessionActive = true;
            }
        } catch (e) { console.log('No existing session, will create on first message.'); }
    })();

    // ===== TODO: Future API hooks =====
    // POST /api/chat — unified chat endpoint (currently using /api/interaction/message)
    // POST /api/voice/stt — send audio blob, get transcript
    // POST /api/voice/tts — send text + voice_name, get audio
    // POST /api/session/summary — get session summary

    // ── Accuracy Dashboard ──────────────────────────────────────
    const accuracyRunBtn = document.getElementById('accuracyRunBtn');
    if (accuracyRunBtn) {
        accuracyRunBtn.addEventListener('click', async () => {
            accuracyRunBtn.disabled = true;
            accuracyRunBtn.textContent = t('accuracy_run_tests') + '...';
            const statusEl = document.getElementById('accuracyStatus');
            if (statusEl) statusEl.textContent = 'Running evaluation...';

            try {
                const res = await fetch('/api/accuracy/evaluate', { method: 'POST' });
                const data = await res.json();
                renderAccuracyResults(data);
                if (statusEl) statusEl.textContent = 'Evaluation complete.';
            } catch (err) {
                console.error('Accuracy evaluation failed:', err);
                if (statusEl) statusEl.textContent = 'Evaluation failed.';
            } finally {
                accuracyRunBtn.disabled = false;
                accuracyRunBtn.textContent = t('accuracy_run_tests');
            }
        });
    }

    // Load accuracy summary when accuracy section is shown
    const advAccuracySection = document.getElementById('adv-accuracy');
    if (advAccuracySection) {
        const observer = new MutationObserver(() => {
            if (advAccuracySection.classList.contains('active')) {
                loadAccuracySummary();
            }
        });
        observer.observe(advAccuracySection, { attributes: true, attributeFilter: ['class'] });
    }

    async function loadAccuracySummary() {
        try {
            const res = await fetch('/api/accuracy/summary');
            const data = await res.json();
            if (data && data.total_interactions > 0) {
                renderAccuracyFromSummary(data);
            } else {
                // Try loading the last report
                const reportRes = await fetch('/api/accuracy/report');
                const report = await reportRes.json();
                if (report && report.overall_accuracy !== undefined) {
                    renderAccuracyResults(report);
                }
            }
        } catch (err) {
            console.log('No accuracy data yet.');
        }
    }

    function renderAccuracyFromSummary(summary) {
        const map = {
            stt: { bar: 'accBarStt', val: 'accValStt', key: 'avg_transcript_confidence' },
            intent: { bar: 'accBarIntent', val: 'accValIntent', key: 'avg_intent_confidence' },
            safety: { bar: 'accBarSafety', val: 'accValSafety', key: 'avg_safety_confidence' },
            tool: { bar: 'accBarTool', val: 'accValTool', key: 'avg_tool_confidence' },
            response: { bar: 'accBarResponse', val: 'accValResponse', key: 'avg_response_confidence' },
        };
        for (const [, cfg] of Object.entries(map)) {
            const pct = Math.round((summary[cfg.key] || 0) * 100);
            setAccuracyBar(cfg.bar, cfg.val, pct);
        }
        const overallPct = Math.round((summary.avg_overall_confidence || 0) * 100);
        setOverallAccuracy(overallPct);
    }

    function renderAccuracyResults(data) {
        if (data.overall_accuracy !== undefined) {
            setOverallAccuracy(Math.round(data.overall_accuracy * 100));
        }
        const catMap = {
            stt_accuracy: { bar: 'accBarStt', val: 'accValStt' },
            intent_classification: { bar: 'accBarIntent', val: 'accValIntent' },
            safety_detection: { bar: 'accBarSafety', val: 'accValSafety' },
            tool_routing: { bar: 'accBarTool', val: 'accValTool' },
            response_relevance: { bar: 'accBarResponse', val: 'accValResponse' },
        };
        const catResults = data.category_results || {};
        for (const [cat, cfg] of Object.entries(catMap)) {
            if (catResults[cat]) {
                const pct = Math.round(catResults[cat].accuracy * 100);
                setAccuracyBar(cfg.bar, cfg.val, pct);
            }
        }
        // Show failures
        const failuresEl = document.getElementById('accuracyFailures');
        const failuresList = document.getElementById('accuracyFailuresList');
        if (failuresEl && failuresList) {
            failuresList.innerHTML = '';
            let hasFailures = false;
            for (const [cat, catData] of Object.entries(data.details || {})) {
                const fails = catData.failures || [];
                fails.forEach(f => {
                    hasFailures = true;
                    const div = document.createElement('div');
                    div.className = 'failure-item';
                    div.textContent = typeof f === 'string' ? f : (f.id || cat) + ': ' + (f.expected || f.error || 'mismatch');
                    failuresList.appendChild(div);
                });
            }
            failuresEl.style.display = hasFailures ? 'block' : 'none';
        }
        // Show suggestions
        const suggEl = document.getElementById('accuracySuggestions');
        const suggList = document.getElementById('accuracySuggestionsList');
        if (suggEl && suggList && data.recommendations) {
            suggList.innerHTML = '';
            data.recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.textContent = rec;
                suggList.appendChild(li);
            });
            suggEl.style.display = data.recommendations.length > 0 ? 'block' : 'none';
        }
    }

    function setOverallAccuracy(pct) {
        const el = document.getElementById('accuracyOverallValue');
        if (!el) return;
        el.textContent = pct + '%';
        el.className = 'accuracy-overall-value ' + (pct >= 90 ? 'acc-green' : pct >= 70 ? 'acc-yellow' : 'acc-red');
    }

    function setAccuracyBar(barId, valId, pct) {
        const bar = document.getElementById(barId);
        const val = document.getElementById(valId);
        if (bar) {
            bar.style.width = pct + '%';
            bar.className = 'acc-bar-fill ' + (pct >= 90 ? 'acc-green' : pct >= 70 ? 'acc-yellow' : 'acc-red');
        }
        if (val) val.textContent = pct + '%';
    }
});
