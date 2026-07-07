// ZARA — Offline AI Emotional Support Assistant
document.addEventListener('DOMContentLoaded', () => {
    // Debounce utility
    function debounce(fn, ms) {
        let timer;
        return function(...args) { clearTimeout(timer); timer = setTimeout(() => fn.apply(this, args), ms); };
    }

    // ===== VIEWPORT HEIGHT FIX (mobile browsers) =====
    function setViewportHeight() {
        document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
    }
    setViewportHeight();
    window.addEventListener('resize', debounce(setViewportHeight, 100));
    window.addEventListener('orientationchange', () => setTimeout(setViewportHeight, 200));

    // ===== VIEWPORT-AWARE RESPONSIVE BEHAVIOR =====
    const mobileQuery = window.matchMedia('(max-width: 640px)');

    function handleResponsiveLayout(e) {
        const isMobile = e.matches;
        const advSidebar = document.querySelector('.advanced-sidebar');
        if (!advSidebar) return;
        if (isMobile) {
            advSidebar.style.display = 'none';
        } else {
            advSidebar.style.display = '';  // clear inline style, let CSS handle
        }
    }
    mobileQuery.addEventListener('change', handleResponsiveLayout);
    handleResponsiveLayout(mobileQuery);

    // ===== STATE =====
    let currentView = 'assistant'; // 'assistant' | 'voice' | 'advanced'
    let currentLanguage = localStorage.getItem('cognitiveMindLanguage') || 'en';
    let companionSessionActive = false;
    let companionSessionId = null;
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
            "voice_barge_in": "Barge-in (Interrupt)",
            "voice_start": "Start Voice Mode",
            "voice_end": "End Voice Mode",
            "voice_paused": "Paused",
            "voice_i_heard": "I heard:",
            "voice_repeat": "Could you say more?",
            "voice_no_stt": "Live transcript not supported. Recording still works.",
            "voice_profile_label": "Zara Voice",
            "voice_profile_soft": "Soft",
            "voice_profile_cute": "Cute",
            "voice_profile_professional": "Professional",
            "voice_profile_night": "Night",
            "voice_preview_btn": "Preview Voice",
            "voice_preview_playing": "Playing preview...",
            "voice_preview_done": "Preview complete",
            "voice_preview_error": "Preview unavailable",
            "live_transcript_header": "Live Transcript:",
            "nav_dashboard": "Dashboard", "nav_emotions": "Emotions", "nav_needs": "Needs",
            "nav_beliefs": "Beliefs", "nav_goals": "Goals", "nav_conflicts": "Inner Conflicts",
            "nav_identity": "Self-Identity", "nav_memory": "Memory", "nav_graph": "Knowledge Graph",
            "nav_debate": "Internal Debate", "nav_simulation": "Future Preview", "nav_history": "Message Zara",
            "nav_thoughts": "Zara Thinking",
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
            "voice_engine": "Voice Engine",
            "voice_engine_auto": "Auto",
            "voice_engine_backend": "Backend Offline Voice",
            "voice_engine_browser": "Browser Voice",
            "voice_engine_active_backend": "Engine: Backend",
            "voice_engine_active_browser": "Engine: Browser",
            "voice_engine_active_text": "Engine: Text Only",
            "voice_backend_unavailable": "Backend voice unavailable. Using browser.",
            "voice_browser_unavailable": "Browser voice unavailable. Text-only mode.",
            "voice_stt_failed": "Speech recognition failed. Try again.",
            "nav_timeline": "Timeline", "title_timeline": "Episodic Timeline",
            "timeline_today": "Today", "timeline_yesterday": "Yesterday",
            "timeline_week": "This Week", "timeline_all": "All",
            "timeline_episodes": "Episodes", "timeline_projects": "Projects",
            "timeline_emotions": "Emotional Journey", "timeline_achievements": "Achievements",
            "timeline_pending": "Pending Goals", "timeline_search_placeholder": "Search episodes...",
            "timeline_no_episodes": "No episodes for this period", "timeline_loading": "Loading...",
            "nav_system_health": "System Health", "title_system_health": "System Health",
            "health_overall": "Overall Health", "health_subsystems": "Subsystems",
            "health_resources": "Resources", "health_degraded": "Degraded Features",
            "health_healthy": "Healthy", "health_degraded_status": "Degraded",
            "health_unavailable": "Unavailable", "health_unknown": "Unknown",
            "health_cpu": "CPU", "health_ram": "RAM", "health_disk": "Disk",
            "health_auto_refresh": "Auto-refresh (10s)", "health_no_degraded": "All systems operational",
            "health_fix_suggestion": "Fix: ", "health_loading": "Loading...", "health_error": "Unable to load",
            "nav_workspace": "Workspace", "title_workspace": "Cognitive Workspace",
            "workspace_active_project": "Active Project", "workspace_tasks": "Tasks",
            "workspace_milestones": "Milestones", "workspace_blocked": "Blocked",
            "workspace_next_action": "Next Action", "workspace_search_placeholder": "Search projects, tasks...",
            "workspace_create_project": "Create Project", "workspace_create_task": "Create Task",
            "workspace_quick_resume": "Quick Resume", "workspace_progress": "Progress",
            "workspace_completed_today": "Completed Today", "workspace_velocity": "Velocity",
            "workspace_health": "Health", "workspace_no_projects": "No active project",
            "workspace_no_tasks": "No tasks ready", "card_header_workspace": "WORKSPACE",
            "workspace_col_pending": "Pending", "workspace_col_in_progress": "In Progress",
            "workspace_col_blocked": "Blocked", "workspace_col_completed": "Completed",
            "workspace_project_name_ph": "Project name", "workspace_project_desc_ph": "Description (optional)",
            "workspace_task_title_ph": "Task title", "workspace_task_desc_ph": "Description (optional)",
            "priority_critical": "Critical",
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
            "voice_take_your_time": "\u09a7\u09c0\u09b0\u09c7 \u09a8\u09bf\u09a8\u0964",
            "voice_thinking": "\u09b8\u09cd\u09a5\u09be\u09a8\u09c0\u09af\u09bc\u09ad\u09be\u09ac\u09c7 \u099a\u09bf\u09a8\u09cd\u09a4\u09be \u0995\u09b0\u099b\u09bf...",
            "voice_interrupted": "\u09ac\u09be\u09a7\u09be \u09a6\u09c7\u0993\u09af\u09bc\u09be \u09b9\u09af\u09bc\u09c7\u099b\u09c7\u0964 \u0986\u09ae\u09bf \u09b6\u09c1\u09a8\u099b\u09bf\u0964",
            "voice_settings": "\u09ad\u09af\u09bc\u09c7\u09b8 \u09b8\u09c7\u099f\u09bf\u0982\u09b8",
            "voice_speed": "\u0995\u09a5\u09be\u09b0 \u0997\u09a4\u09bf",
            "voice_volume": "\u09ad\u09b2\u09bf\u0989\u09ae",
            "voice_continuous": "\u0995\u09cd\u09b0\u09ae\u09be\u0997\u09a4 \u09b6\u09cd\u09b0\u09ac\u09a3",
            "voice_playback_speed": "\u09aa\u09cd\u09b2\u09c7\u09ac\u09cd\u09af\u09be\u0995 \u0997\u09a4\u09bf",
            "voice_barge_in": "\u09ac\u09be\u09a7\u09be (\u0987\u09a8\u09cd\u099f\u09be\u09b0\u09aa\u09cd\u099f)",
            "voice_start": "\u09ad\u09af\u09bc\u09c7\u09b8 \u09ae\u09cb\u09a1 \u09b6\u09c1\u09b0\u09c1 \u0995\u09b0\u09c1\u09a8",
            "voice_end": "\u09ad\u09af\u09bc\u09c7\u09b8 \u09ae\u09cb\u09a1 \u09ac\u09a8\u09cd\u09a7 \u0995\u09b0\u09c1\u09a8",
            "voice_paused": "\u09b8\u09cd\u09a5\u0997\u09bf\u09a4",
            "voice_i_heard": "\u0986\u09ae\u09bf \u09b6\u09c1\u09a8\u09c7\u099b\u09bf:",
            "voice_repeat": "\u0986\u09b0\u0993 \u09ac\u09b2\u09a4\u09c7 \u09aa\u09be\u09b0\u09c7\u09a8?",
            "voice_no_stt": "\u09b2\u09be\u0987\u09ad \u099f\u09cd\u09b0\u09be\u09a8\u09cd\u09b8\u0995\u09cd\u09b0\u09bf\u09aa\u09cd\u099f \u09b8\u09ae\u09b0\u09cd\u09a5\u09bf\u09a4 \u09a8\u09df\u0964",
            "voice_profile_label": "\u099d\u09be\u09b0\u09be\u09b0 \u09ad\u09af\u09bc\u09c7\u09b8",
            "voice_profile_soft": "\u09b8\u09ab\u099f",
            "voice_profile_cute": "\u0995\u09bf\u0989\u099f",
            "voice_profile_professional": "\u09aa\u09cd\u09b0\u09ab\u09c7\u09b6\u09a8\u09be\u09b2",
            "voice_profile_night": "\u09a8\u09be\u0987\u099f",
            "voice_preview_btn": "\u09ad\u09af\u09bc\u09c7\u09b8 \u09aa\u09cd\u09b0\u09bf\u09ad\u09bf\u0989",
            "voice_preview_playing": "\u09aa\u09cd\u09b0\u09bf\u09ad\u09bf\u0989 \u099a\u09b2\u099b\u09c7...",
            "voice_preview_done": "\u09aa\u09cd\u09b0\u09bf\u09ad\u09bf\u0989 \u09b8\u09ae\u09cd\u09aa\u09a8\u09cd\u09a8",
            "voice_preview_error": "\u09aa\u09cd\u09b0\u09bf\u09ad\u09bf\u0989 \u09aa\u09be\u0993\u09af\u09bc\u09be \u09af\u09be\u099a\u09cd\u099b\u09c7 \u09a8\u09be",
            "live_transcript_header": "\u09b2\u09be\u0987\u09ad \u09aa\u09cd\u09b0\u09a4\u09bf\u09b2\u09bf\u09aa\u09bf:",
            "nav_dashboard": "ড্যাশবোর্ড", "nav_emotions": "আবেগ", "nav_needs": "প্রয়োজন",
            "nav_beliefs": "বিশ্বাস", "nav_goals": "লক্ষ্য", "nav_conflicts": "অভ্যন্তরীণ দ্বন্দ্ব",
            "nav_identity": "আত্ম-পরিচয়", "nav_memory": "স্মৃতি", "nav_graph": "জ্ঞান গ্রাফ",
            "nav_debate": "\u0985\u09ad\u09cd\u09af\u09a8\u09cd\u09a4\u09b0\u09c0\u09a3 \u09ac\u09bf\u09a4\u09b0\u09cd\u0995", "nav_simulation": "\u09ad\u09ac\u09bf\u09b7\u09cd\u09af\u09ce \u09aa\u09cd\u09b0\u09bf\u09ad\u09bf\u0989", "nav_history": "\u099d\u09be\u09b0\u09be \u0995\u09c7 \u09ac\u09be\u09b0\u09cd\u09a4\u09be",
            "nav_thoughts": "\u099d\u09be\u09b0\u09be\u09b0 \u099a\u09bf\u09a8\u09cd\u09a4\u09be",
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
            "voice_engine": "\u09ad\u09af\u09bc\u09b8 \u0987\u099e\u09cd\u099c\u09bf\u09a8",
            "voice_engine_auto": "\u09b8\u09cd\u09ac\u09af\u09bc\u0982\u0995\u09cd\u09b0\u09bf\u09af\u09bc",
            "voice_engine_backend": "\u09ac\u09cd\u09af\u09be\u0995\u098f\u0982\u09a1 \u0985\u09ab\u09b2\u09be\u0987\u09a8 \u09ad\u09af\u09bc\u09b8",
            "voice_engine_browser": "\u09ac\u09cd\u09b0\u09be\u0989\u099c\u09be\u09b0 \u09ad\u09af\u09bc\u09b8",
            "voice_engine_active_backend": "\u0987\u099e\u09cd\u099c\u09bf\u09a8: \u09ac\u09cd\u09af\u09be\u0995\u098f\u0982\u09a1",
            "voice_engine_active_browser": "\u0987\u099e\u09cd\u099c\u09bf\u09a8: \u09ac\u09cd\u09b0\u09be\u0989\u099c\u09be\u09b0",
            "voice_engine_active_text": "\u0987\u099e\u09cd\u099c\u09bf\u09a8: \u0995\u09c7\u09ac\u09b2 \u099f\u09c7\u0995\u09cd\u09b8\u099f",
            "voice_backend_unavailable": "\u09ac\u09cd\u09af\u09be\u0995\u098f\u0982\u09a1 \u09ad\u09af\u09bc\u09b8 \u09aa\u09be\u0993\u09af\u09bc\u09be \u09af\u09be\u099a\u09cd\u099b\u09c7 \u09a8\u09be\u0964 \u09ac\u09cd\u09b0\u09be\u0989\u099c\u09be\u09b0 \u09ac\u09cd\u09af\u09ac\u09b9\u09be\u09b0 \u0995\u09b0\u09be \u09b9\u099a\u09cd\u099b\u09c7\u0964",
            "voice_browser_unavailable": "\u09ac\u09cd\u09b0\u09be\u0989\u099c\u09be\u09b0 \u09ad\u09af\u09bc\u09b8 \u09aa\u09be\u0993\u09af\u09bc\u09be \u09af\u09be\u099a\u09cd\u099b\u09c7 \u09a8\u09be\u0964 \u0995\u09c7\u09ac\u09b2 \u099f\u09c7\u0995\u09cd\u09b8\u099f \u09ae\u09cb\u09a1\u0964",
            "voice_stt_failed": "\u09b8\u09cd\u09aa\u09c0\u099a \u09b8\u09cd\u09ac\u09c0\u0995\u09c3\u09a4\u09bf \u09ac\u09cd\u09af\u09b0\u09cd\u09a5\u0964 \u0986\u09ac\u09be\u09b0 \u099a\u09c7\u09b7\u09cd\u099f\u09be \u0995\u09b0\u09c1\u09a8\u0964",
            "nav_timeline": "\u099f\u09be\u0987\u09ae\u09b2\u09be\u0987\u09a8", "title_timeline": "\u09aa\u09be\u09b0\u09cd\u09ac\u09a8\u09bf\u0995 \u099f\u09be\u0987\u09ae\u09b2\u09be\u0987\u09a8",
            "timeline_today": "\u0986\u099c", "timeline_yesterday": "\u0997\u09a4\u0995\u09be\u09b2",
            "timeline_week": "\u098f\u0987 \u09b8\u09aa\u09cd\u09a4\u09be\u09b9", "timeline_all": "\u09b8\u09ac",
            "timeline_episodes": "\u09aa\u09b0\u09cd\u09ac", "timeline_projects": "\u09aa\u09cd\u09b0\u099c\u09c7\u0995\u09cd\u099f",
            "timeline_emotions": "\u0986\u09ac\u09c7\u0997\u09bf\u0995 \u09af\u09be\u09a4\u09cd\u09b0\u09be", "timeline_achievements": "\u0985\u09b0\u09cd\u099c\u09a8",
            "timeline_pending": "\u09ac\u09be\u0995\u09bf \u09b2\u0995\u09cd\u09b7\u09cd\u09af", "timeline_search_placeholder": "\u09aa\u09b0\u09cd\u09ac \u0985\u09a8\u09c1\u09b8\u09a8\u09cd\u09a7\u09be\u09a8...",
            "timeline_no_episodes": "\u098f\u0987 \u09b8\u09ae\u09af\u09bc\u09c7\u09b0 \u0995\u09c7\u09be\u09a8 \u09aa\u09b0\u09cd\u09ac \u09a8\u09c7\u0987", "timeline_loading": "\u09b2\u09c7\u09be\u09a1 \u09b9\u099a\u09cd\u099b\u09c7...",
            "nav_system_health": "\u09b8\u09bf\u09b8\u09cd\u099f\u09c7\u09ae \u09b8\u09cd\u09ac\u09be\u09b8\u09cd\u09a5\u09cd\u09af",
            "title_system_health": "\u09b8\u09bf\u09b8\u09cd\u099f\u09c7\u09ae \u09b8\u09cd\u09ac\u09be\u09b8\u09cd\u09a5\u09cd\u09af",
            "health_overall": "\u09b8\u09be\u09ae\u0997\u09cd\u09b0\u09bf\u0995 \u09b8\u09cd\u09ac\u09be\u09b8\u09cd\u09a5\u09cd\u09af",
            "health_subsystems": "\u09b8\u09be\u09ac\u09b8\u09bf\u09b8\u09cd\u099f\u09c7\u09ae",
            "health_resources": "\u09b8\u09ae\u09cd\u09aa\u09a6",
            "health_degraded": "\u0985\u09ac\u09a8\u09ae\u09bf\u09a4 \u09ac\u09c8\u09b6\u09bf\u09b7\u09cd\u099f\u09cd\u09af",
            "health_healthy": "\u09b8\u09c1\u09b8\u09cd\u09a5",
            "health_degraded_status": "\u0985\u09ac\u09a8\u09ae\u09bf\u09a4",
            "health_unavailable": "\u0985\u09a8\u09c1\u09aa\u09b2\u09ac\u09cd\u09a7",
            "health_unknown": "\u0985\u099c\u09be\u09a8\u09be",
            "health_cpu": "\u09b8\u09bf\u09aa\u09bf\u0987\u0989",
            "health_ram": "\u09b0\u09cd\u09af\u09be\u09ae",
            "health_disk": "\u09a1\u09bf\u09b8\u09cd\u0995",
            "health_auto_refresh": "\u09b8\u09cd\u09ac\u09af\u09bc\u0982\u0995\u09cd\u09b0\u09bf\u09af\u09bc \u09b0\u09bf\u09ab\u09cd\u09b0\u09c7\u09b6 (\u09e7\u09e6\u09b8\u09c7)",
            "health_no_degraded": "\u09b8\u09ac \u09b8\u09bf\u09b8\u09cd\u099f\u09c7\u09ae \u09b8\u09cd\u09ac\u09be\u09ad\u09be\u09ac\u09bf\u0995",
            "health_fix_suggestion": "\u09b8\u09ae\u09be\u09a7\u09be\u09a8: ",
            "health_loading": "\u09b2\u09c7\u09be\u09a1 \u09b9\u099a\u09cd\u099b\u09c7...",
            "health_error": "\u09b2\u09c7\u09be\u09a1 \u0995\u09b0\u09be \u09af\u09be\u099a\u09cd\u099b\u09c7 \u09a8\u09be",
            "nav_workspace": "\u0993\u09af\u09bc\u09be\u09b0\u09cd\u0995\u09b8\u09cd\u09aa\u09c7\u09b8",
            "title_workspace": "\u0995\u0997\u09a8\u09bf\u099f\u09bf\u09ad \u0993\u09af\u09bc\u09be\u09b0\u09cd\u0995\u09b8\u09cd\u09aa\u09c7\u09b8",
            "workspace_active_project": "\u09b8\u0995\u09cd\u09b0\u09bf\u09af\u09bc \u09aa\u09cd\u09b0\u099c\u09c7\u0995\u09cd\u099f",
            "workspace_tasks": "\u0995\u09be\u099c", "workspace_milestones": "\u09ae\u09be\u0987\u09b2\u09ab\u09b2\u0995",
            "workspace_blocked": "\u0986\u099f\u0995\u09be\u09a8\u09c7", "workspace_next_action": "\u09aa\u09b0\u09ac\u09b0\u09cd\u09a4\u09c0 \u0995\u09be\u099c",
            "workspace_search_placeholder": "\u09aa\u09cd\u09b0\u099c\u09c7\u0995\u09cd\u099f, \u0995\u09be\u099c \u0985\u09a8\u09c1\u09b8\u09a8\u09cd\u09a7\u09be\u09a8...",
            "workspace_create_project": "\u09aa\u09cd\u09b0\u099c\u09c7\u0995\u09cd\u099f \u09a4\u09c8\u09b0\u09bf",
            "workspace_create_task": "\u0995\u09be\u099c \u09a4\u09c8\u09b0\u09bf",
            "workspace_quick_resume": "\u09a6\u09cd\u09b0\u09c1\u09a4 \u09aa\u09c1\u09a8\u09b0\u09be\u09af\u09bc",
            "workspace_progress": "\u0985\u0997\u09cd\u09b0\u0997\u09a4\u09bf",
            "workspace_completed_today": "\u0986\u099c \u09b8\u09ae\u09cd\u09aa\u09a8\u09cd\u09a8",
            "workspace_velocity": "\u0997\u09a4\u09bf", "workspace_health": "\u09b8\u09cd\u09ac\u09be\u09b8\u09cd\u09a5\u09cd\u09af",
            "workspace_no_projects": "\u0995\u09c7\u09be\u09a8 \u09b8\u0995\u09cd\u09b0\u09bf\u09af\u09bc \u09aa\u09cd\u09b0\u099c\u09c7\u0995\u09cd\u099f \u09a8\u09c7\u0987",
            "workspace_no_tasks": "\u0995\u09c7\u09be\u09a8 \u0995\u09be\u099c \u09aa\u09cd\u09b0\u09b8\u09cd\u09a4\u09c1\u09a4 \u09a8\u09c7\u0987",
            "card_header_workspace": "\u0993\u09af\u09bc\u09be\u09b0\u09cd\u0995\u09b8\u09cd\u09aa\u09c7\u09b8",
            "workspace_col_pending": "\u0985\u09aa\u09c7\u0995\u09cd\u09b7\u09be\u09ae\u09be\u09a8",
            "workspace_col_in_progress": "\u099a\u09b2\u099b\u09c7",
            "workspace_col_blocked": "\u0986\u099f\u0995\u09be\u09a8\u09c7",
            "workspace_col_completed": "\u09b8\u09ae\u09cd\u09aa\u09a8\u09cd\u09a8",
            "workspace_project_name_ph": "\u09aa\u09cd\u09b0\u099c\u09c7\u0995\u09cd\u099f\u09c7\u09b0 \u09a8\u09be\u09ae",
            "workspace_project_desc_ph": "\u09ac\u09bf\u09ac\u09b0\u09a3 (\u0990\u099a\u09cd\u099b\u09bf\u0995)",
            "workspace_task_title_ph": "\u0995\u09be\u099c\u09c7\u09b0 \u09b6\u09bf\u09b0\u09c7\u09be\u09a8\u09be\u09ae",
            "workspace_task_desc_ph": "\u09ac\u09bf\u09ac\u09b0\u09a3 (\u0990\u099a\u09cd\u099b\u09bf\u0995)",
            "priority_critical": "\u099c\u09b0\u09c1\u09b0\u09bf",
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

    // Agent mode state
    const VALID_AGENT_MODES = ['assistant', 'psychologist', 'coding', 'project', 'prediction', 'safety', 'night'];
    const MANUAL_MODES = ['assistant', 'psychologist', 'coding', 'project', 'prediction', 'night'];
    const MODE_LABELS = {
        assistant: 'Assistant',
        psychologist: 'Support',
        coding: 'Coding',
        project: 'Project',
        prediction: 'Prediction',
        safety: 'Safety',
        night: 'Night',
    };

    const modeSelector = document.getElementById('modeSelector');
    const nightModeToggle = document.getElementById('nightModeToggle');

    // Night mode state
    let nightModeActive = localStorage.getItem('zaraNightMode') === 'true';

    function setAgentMode(mode) {
        if (!VALID_AGENT_MODES.includes(mode)) mode = 'assistant';
        // Safety mode cannot be manually set
        if (mode === 'safety') return;
        currentMode = mode;
        localStorage.setItem('zaraAgentMode', mode);
        updateModeSelector();
        updateProfileForMode();
        applyNightMode(mode === 'night');
    }

    function updateModeSelector() {
        if (modeSelector) {
            modeSelector.value = MANUAL_MODES.includes(currentMode) ? currentMode : 'assistant';
        }
    }

    function applyNightMode(enable) {
        nightModeActive = enable;
        localStorage.setItem('zaraNightMode', String(enable));
        if (enable) {
            document.body.classList.add('night-mode');
        } else {
            document.body.classList.remove('night-mode');
        }
        if (nightModeToggle) {
            nightModeToggle.classList.toggle('active', enable);
        }
        // Update night voice status in settings panel
        if (typeof updateNightVoiceStatus === 'function') {
            updateNightVoiceStatus();
        }
    }

    // Mode selector dropdown change
    if (modeSelector) {
        modeSelector.addEventListener('change', () => {
            const selected = modeSelector.value;
            setAgentMode(selected);
        });
    }

    // Night mode toggle button
    if (nightModeToggle) {
        nightModeToggle.addEventListener('click', () => {
            if (nightModeActive) {
                // Turn off night mode — revert to previous non-night mode
                const prevMode = localStorage.getItem('zaraPrevMode') || 'assistant';
                setAgentMode(prevMode);
            } else {
                // Save current mode, switch to night
                if (currentMode !== 'night') {
                    localStorage.setItem('zaraPrevMode', currentMode);
                }
                setAgentMode('night');
            }
        });
    }

    function updateProfileForMode() {
        // Auto-update voice profile when mode changes (if auto emotional voice is on)
        if (autoEmotionalVoice && voiceProfileSelect) {
            const modeToProfile = {
                assistant: 'zara_cute',
                psychologist: 'zara_soft',
                coding: 'zara_professional',
                project: 'zara_professional',
                prediction: 'zara_professional',
                safety: 'zara_professional',
                night: 'zara_night',
            };
            const newProfile = modeToProfile[currentMode] || 'zara_soft';
            currentVoiceProfile = newProfile;
            voiceProfileSelect.value = newProfile;
            updateProfileDescription();
        }
    }

    // --- Volume & Speed Helpers ---
    function getEffectiveVolume() {
        // Base volume from slider (default 0.9)
        const slider = document.getElementById('voiceVolumeSlider');
        let base = slider ? (slider.value / 100) : 0.9;
        // Night mode caps at 0.7
        if (nightModeActive) {
            base = Math.min(base, 0.7);
        }
        return Math.max(0.1, Math.min(1.0, base));
    }

    function getEffectiveSpeed() {
        // Speed from speed buttons or slider (default 1.0)
        const speedBtn = document.querySelector('.speed-btn.active');
        let base = speedBtn ? parseFloat(speedBtn.dataset.speed) : 1.0;
        // Night mode slows down
        if (nightModeActive) {
            base = Math.min(base, 0.85);
        }
        return Math.max(0.5, Math.min(2.0, base));
    }

    function showView(name) {
        assistantView.classList.remove('active');
        advancedView.classList.remove('active');
        voiceView.classList.remove('active');
        currentView = name;
        if (name === 'assistant') assistantView.classList.add('active');
        else if (name === 'voice') voiceView.classList.add('active');
        else if (name === 'advanced') advancedView.classList.add('active');
        // Set mode based on view
        if (name === 'assistant') setAgentMode('assistant');
        else if (name === 'voice') setAgentMode('psychologist');
        else if (name === 'advanced') setAgentMode('project');
    }

    document.getElementById('voiceModeBtn').addEventListener('click', () => { showView('voice'); if (voiceState === VoiceState.IDLE) startVoiceMode(); });
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
                body: JSON.stringify({ text, language: currentLanguage, speak_response: speakResponseToggle.checked, mode: currentMode })
            });
            const result = await res.json();
            removeTypingIndicator();
            // Update mode from backend response if resolved differently
            if (result.resolved_mode && result.resolved_mode !== currentMode) {
                // Safety mode is automatic only — don't persist it
                if (result.resolved_mode === 'safety') {
                    // Temporarily show safety but don't change saved mode
                    currentMode = 'safety';
                    updateModeSelector();
                    updateProfileForMode();
                } else {
                    setAgentMode(result.resolved_mode);
                }
            }
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

    // ===== VOICE MODE — Full Rewrite =====
    // --- Configurable Constants ---
    const VOICE_CONFIG = {
        SILENCE_IGNORE_MS: 1200,      // ignore silence under this
        SILENCE_THINKING_MS: 4000,    // thinking pause threshold
        SILENCE_LONG_MS: 7000,        // long pause -> finalize
        SILENCE_SHORT_TRANSCRIPT_MS: 9000, // wait longer if transcript is very short
        SHORT_TRANSCRIPT_WORDS: 3,    // below this = short transcript
        IMMEDIATE_FINALIZE_PHRASES: ['go ahead', 'answer now', "that's all", 'that is all', '\u0986\u09ae\u09bf \u09b6\u09c7\u09b7'],
        NOISE_CALIBRATION_MS: 1000,
        SPEECH_THRESHOLD_MULTIPLIER: 2.5, // above noise floor = speech
        MIN_SPEECH_DURATION_MS: 150,
        MIN_SILENCE_DURATION_MS: 100,
    };

    // --- Voice State ---
    const VoiceState = { IDLE:'idle', LISTENING:'listening', USER_SPEAKING:'user_speaking', USER_PAUSED:'user_paused', FINALIZING:'finalizing', PROCESSING:'processing', SPEAKING:'speaking' };
    let voiceState = VoiceState.IDLE;
    let voiceActive = false; // mic + recognition running
    let finalTranscript = '';
    let interimTranscript = '';
    let lastResponseText = '';
    let silenceTimers = [];
    let silenceStart = 0;
    let speechStart = 0;
    let isCalibrating = false;
    let noiseFloor = 0.01;
    let audioContext = null;
    let analyserNode = null;
    let micStream = null;
    let vadAnimFrame = null;
    let recognition = null;
    let recognitionActive = false;
    let synthUtterance = null;
    let synthPaused = false;
    let backendAvailable = false;
    let backendCheckInterval = null;
    let voiceEngineMode = 'auto'; // 'auto' | 'backend' | 'browser'
    let activeVoiceEngine = 'browser'; // resolved: 'backend' | 'browser' | 'text'
    let currentMode = localStorage.getItem('zaraAgentMode') || 'assistant'; // Agent mode
    let currentVoiceProfile = 'zara_soft'; // 'zara_soft' | 'zara_cute' | 'zara_professional' | 'zara_night'
    let backendSTTAvailable = false;
    let backendTTSAvailable = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let backendAudioElement = null;
    let backendAudioPlaying = false;

    // --- DOM refs ---
    const voiceOrb = document.getElementById('voiceOrb');
    const voiceStateText = document.getElementById('voiceStateText');
    const voiceTranscript = document.getElementById('voiceTranscript');
    const voiceTranscriptText = document.getElementById('voiceTranscriptText');
    const voiceMeter = document.getElementById('voiceMeter');
    const voiceMeterFill = document.getElementById('voiceMeterFill');
    const voiceMainBtn = document.getElementById('voiceMainBtn');
    const voicePauseBtn = document.getElementById('voicePauseBtn');
    const voiceResumeBtn = document.getElementById('voiceResumeBtn');
    const voiceStopBtn = document.getElementById('voiceStopBtn');
    const voiceReplayBtn = document.getElementById('voiceReplayBtn');
    const voiceResponseText = document.getElementById('voiceResponseText');
    const voiceSpeedControls = document.getElementById('voiceSpeedControls');
    const voiceVolumeSlider = document.getElementById('voiceVolumeSlider');
    const voiceSettingsToggle = document.getElementById('voiceSettingsToggle');
    const voiceSettingsPanel = document.getElementById('voiceSettingsPanel');
    const voiceContinuousToggle = document.getElementById('voiceContinuousToggle');
    const voiceBargeInToggle = document.getElementById('voiceBargeInToggle');
    const voiceProfileSelect = document.getElementById('voiceProfileSelect');
    const voiceProfileDesc = document.getElementById('voiceProfileDesc');
    const voicePreviewBtn = document.getElementById('voicePreviewBtn');
    const voicePreviewStatus = document.getElementById('voicePreviewStatus');
    const voiceAutoEmotionalToggle = document.getElementById('voiceAutoEmotionalToggle');
    const voiceSpeakingIndicator = document.getElementById('voiceSpeakingIndicator');
    const speakingStatusText = document.getElementById('speakingStatusText');
    const speakingSentenceText = document.getElementById('speakingSentenceText');
    const voicePreviewSample = document.getElementById('voicePreviewSample');

    // Auto emotional voice state
    let autoEmotionalVoice = true;

    // Preview sample texts
    const previewSampleTexts = {
        'friendly': "Hey there! I'm Zara. How can I help you today?",
        'supportive': "Hi, I'm Zara. I'm here with you. Take your time.",
        'professional': "Hello. I'm Zara. Let's focus on the task at hand.",
        'night': "Hi... I'm Zara. It's okay to rest. I'm here.",
    };

    // Speaking style status messages
    const styleStatusMessages = {
        'calm_support': 'Zara is speaking in support mode...',
        'friendly_assistant': 'Zara is speaking softly...',
        'professional_clear': 'Zara is speaking clearly...',
        'night_soft': 'Zara is speaking gently...',
        'emergency_clear': 'Zara is speaking directly...',
    };

    // Voice profile descriptions
    const voiceProfileDescriptions = {
        'zara_soft': 'Warm, calm voice for support conversations',
        'zara_cute': 'Bright, friendly assistant voice',
        'zara_professional': 'Clear, professional voice',
        'zara_night': 'Soft, quiet voice for night use',
    };

    // --- Initialize mode + night mode from localStorage ---
    (function initModeState() {
        // Restore saved agent mode
        const savedMode = localStorage.getItem('zaraAgentMode') || 'assistant';
        if (VALID_AGENT_MODES.includes(savedMode) && savedMode !== 'safety') {
            currentMode = savedMode;
        }
        // Restore night mode
        const savedNight = localStorage.getItem('zaraNightMode') === 'true';
        if (savedNight || currentMode === 'night') {
            applyNightMode(true);
        }
        // Sync dropdown
        updateModeSelector();
        updateProfileForMode();
    })();

    // --- Backend Connectivity ---
    async function checkBackendHealth() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);
            const res = await fetch('/api/health', { signal: controller.signal });
            clearTimeout(timeoutId);
            const data = await res.json();
            const wasOffline = !backendAvailable;
            backendAvailable = data.status === 'healthy';
            if (wasOffline && backendAvailable) {
                logVoice('Backend came online');
                if (voiceState === VoiceState.IDLE && voiceActive) {
                    voiceStateText.textContent = t('voice_listening');
                }
            }
            return backendAvailable;
        } catch (e) {
            backendAvailable = false;
            return false;
        }
    }

    async function syncVoiceState(backendState, reason) {
        if (!backendAvailable) return;
        try {
            await fetch('/api/voice/state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ state: backendState, reason: reason || 'frontend_state_change' })
            });
        } catch (e) {
            logVoice('Voice state sync failed: ' + e.message);
        }
    }

    function startBackendHealthMonitor() {
        checkBackendHealth();
        backendCheckInterval = setInterval(checkBackendHealth, 15000);
    }

    function stopBackendHealthMonitor() {
        if (backendCheckInterval) { clearInterval(backendCheckInterval); backendCheckInterval = null; }
    }

    // --- Voice Engine Detection ---
    async function detectBackendVoiceEngines() {
        if (!backendAvailable) {
            backendSTTAvailable = false;
            backendTTSAvailable = false;
            return;
        }
        try {
            const res = await fetch('/api/voice/engines');
            const data = await res.json();
            backendSTTAvailable = data.stt && data.stt.available;
            backendTTSAvailable = data.tts && data.tts.available;
            logVoice('Backend voice engines: STT=' + backendSTTAvailable + ' TTS=' + backendTTSAvailable);
        } catch (e) {
            backendSTTAvailable = false;
            backendTTSAvailable = false;
        }
        resolveActiveEngine();
    }

    function resolveActiveEngine() {
        const indicator = document.getElementById('voiceEngineIndicator');
        if (voiceEngineMode === 'backend') {
            if (backendSTTAvailable || backendTTSAvailable) {
                activeVoiceEngine = 'backend';
                if (indicator) indicator.textContent = t('voice_engine_active_backend');
            } else {
                activeVoiceEngine = 'text';
                if (indicator) indicator.textContent = t('voice_engine_active_text');
            }
        } else if (voiceEngineMode === 'browser') {
            activeVoiceEngine = 'browser';
            if (indicator) indicator.textContent = t('voice_engine_active_browser');
        } else {
            // Auto mode: prefer backend, fallback to browser
            if (backendSTTAvailable || backendTTSAvailable) {
                activeVoiceEngine = 'backend';
                if (indicator) indicator.textContent = t('voice_engine_active_backend');
            } else if (window.SpeechRecognition || window.webkitSpeechRecognition || window.speechSynthesis) {
                activeVoiceEngine = 'browser';
                if (indicator) indicator.textContent = t('voice_engine_active_browser');
            } else {
                activeVoiceEngine = 'text';
                if (indicator) indicator.textContent = t('voice_engine_active_text');
            }
        }
        logVoice('Active voice engine: ' + activeVoiceEngine);
    }

    // --- Backend STT (MediaRecorder → /api/voice/stt) ---
    async function startBackendRecording() {
        try {
            if (!micStream) {
                micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            }
            audioChunks = [];
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : 'audio/webm';
            mediaRecorder = new MediaRecorder(micStream, { mimeType: mimeType });
            mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
            mediaRecorder.onstop = async () => {
                if (audioChunks.length === 0) return;
                const audioBlob = new Blob(audioChunks, { type: mimeType });
                await sendAudioToBackendSTT(audioBlob);
            };
            mediaRecorder.start(250); // Collect data every 250ms
            logVoice('Backend recording started');
            return true;
        } catch (e) {
            logVoice('Backend recording failed: ' + e.message);
            return false;
        }
    }

    function stopBackendRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            logVoice('Backend recording stopped');
        }
    }

    async function sendAudioToBackendSTT(audioBlob) {
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');
        formData.append('language', currentLanguage);
        try {
            const res = await fetch('/api/voice/stt', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();
            if (result.success && result.transcript) {
                finalTranscript = result.transcript;
                voiceTranscriptText.textContent = result.transcript;
                logVoice('Backend STT transcript: ' + result.transcript);
                // Send to voice transcript + chat
                await sendVoiceMessage(result.transcript);
            } else {
                logVoice('Backend STT failed: ' + (result.errors || ['unknown']).join(', '));
                handleSTTFallback();
            }
        } catch (e) {
            logVoice('Backend STT error: ' + e.message);
            handleSTTFallback();
        }
    }

    function handleSTTFallback() {
        // Fallback to browser SpeechRecognition if available
        if (activeVoiceEngine === 'backend' && (window.SpeechRecognition || window.webkitSpeechRecognition)) {
            voiceStateText.textContent = t('voice_backend_unavailable');
            startRecognition();
        } else {
            voiceStateText.textContent = t('voice_stt_failed');
            setTimeout(() => { if (voiceActive) setVoiceState(VoiceState.LISTENING); }, 2000);
        }
    }

    // --- Backend TTS (/api/voice/tts → HTMLAudioElement) ---
    async function speakResponseBackend(text) {
        if (!backendTTSAvailable) return false;
        try {
            // Determine emotion context based on auto mode
            let emotionCtx = null;
            let speakingStyle = null;
            if (autoEmotionalVoice) {
                // Map current app mode to emotion context
                const modeMap = {
                    psychologist: 'support',
                    assistant: 'chat',
                    coding: 'coding',
                    project: 'coding',
                    prediction: 'coding',
                    safety: 'crisis',
                    night: 'night'
                };
                emotionCtx = modeMap[currentMode] || 'chat';
            }

            // Signal backend to arm EchoGuard
            fetch('/api/voice/playback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'speak', text: text, language: currentLanguage })
            }).catch(() => {});

            const ttsPayload = {
                text: text,
                voice: 'female',
                voice_profile: currentVoiceProfile,
                language: currentLanguage,
                speed: getEffectiveSpeed(),
                volume: getEffectiveVolume(),
                night_mode: nightModeActive
            };
            if (emotionCtx) ttsPayload.emotion_context = emotionCtx;
            if (speakingStyle) ttsPayload.speaking_style = speakingStyle;

            const res = await fetch('/api/voice/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(ttsPayload)
            });

            if (!res.ok) {
                logVoice('Backend TTS returned ' + res.status);
                return false;
            }

            const contentType = res.headers.get('content-type') || '';
            if (contentType.includes('audio')) {
                // Show speaking indicator
                const styleHeader = res.headers.get('X-TTS-Style') || 'calm_support';
                showSpeakingIndicator(styleHeader, text);

                // Play audio via HTMLAudioElement
                const audioUrl = URL.createObjectURL(await res.blob());
                if (backendAudioElement) {
                    backendAudioElement.pause();
                    URL.revokeObjectURL(backendAudioElement.src);
                }
                backendAudioElement = new Audio(audioUrl);
                // Apply volume from backend metadata or frontend effective volume
                const appliedVolHeader = res.headers.get('X-Zara-Applied-Volume');
                backendAudioElement.volume = appliedVolHeader ? parseFloat(appliedVolHeader) : getEffectiveVolume();
                backendAudioPlaying = true;
                setVoiceState(VoiceState.SPEAKING);

                backendAudioElement.onended = () => {
                    backendAudioPlaying = false;
                    URL.revokeObjectURL(audioUrl);
                    hideSpeakingIndicator();
                    // Disarm EchoGuard
                    fetch('/api/voice/playback', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'stop' })
                    }).catch(() => {});
                    if (voiceActive) {
                        setVoiceState(VoiceState.LISTENING);
                        finalTranscript = '';
                        interimTranscript = '';
                        voiceTranscriptText.textContent = '';
                    } else {
                        setVoiceState(VoiceState.IDLE);
                    }
                };
                backendAudioElement.onerror = () => {
                    backendAudioPlaying = false;
                    URL.revokeObjectURL(audioUrl);
                    hideSpeakingIndicator();
                    if (voiceActive) setVoiceState(VoiceState.LISTENING);
                };
                await backendAudioElement.play();
                return true;
            } else {
                // Non-audio response (JSON error)
                logVoice('Backend TTS did not return audio');
                return false;
            }
        } catch (e) {
            logVoice('Backend TTS error: ' + e.message);
            return false;
        }
    }

    function stopBackendAudio() {
        if (backendAudioElement) {
            backendAudioElement.pause();
            backendAudioPlaying = false;
        }
    }

    // --- State Machine ---
    function logVoice(msg) { console.log('[VOICE ' + new Date().toISOString().substr(11,12) + '] ' + msg); }

    function setVoiceState(newState) {
        const old = voiceState;
        voiceState = newState;
        voiceView.setAttribute('data-state', newState);
        logVoice(old + ' -> ' + newState);

        const stateLabels = {
            idle: 'voice_idle', listening: 'voice_listening',
            user_speaking: 'voice_listening', user_paused: 'voice_take_your_time',
            finalizing: 'voice_processing', processing: 'voice_processing',
            speaking: 'voice_speaking'
        };
        voiceStateText.textContent = t(stateLabels[newState] || 'voice_idle');

        // Sync state to backend voice agent
        const backendStateMap = {
            idle: 'IDLE', listening: 'LISTENING', user_speaking: 'USER_SPEAKING',
            user_paused: 'USER_PAUSED', finalizing: 'FINALIZING',
            processing: 'PROCESSING', speaking: 'SPEAKING'
        };
        if (backendStateMap[newState]) {
            syncVoiceState(backendStateMap[newState], 'frontend_transition');
        }

        // Orb class
        voiceMainBtn.classList.toggle('recording', [VoiceState.LISTENING, VoiceState.USER_SPEAKING, VoiceState.USER_PAUSED].includes(newState));

        // Show/hide transcript & meter
        const showTranscript = [VoiceState.LISTENING, VoiceState.USER_SPEAKING, VoiceState.USER_PAUSED, VoiceState.FINALIZING].includes(newState);
        voiceTranscript.style.display = showTranscript ? 'block' : 'none';
        voiceMeter.style.display = [VoiceState.LISTENING, VoiceState.USER_SPEAKING].includes(newState) ? 'block' : 'none';

        // Show/hide control buttons
        const isRunning = newState !== VoiceState.IDLE;
        voicePauseBtn.style.display = (newState === VoiceState.SPEAKING && !synthPaused) ? 'flex' : 'none';
        voiceResumeBtn.style.display = (newState === VoiceState.SPEAKING && synthPaused) ? 'flex' : 'none';
        voiceStopBtn.style.display = isRunning ? 'flex' : 'none';
        voiceReplayBtn.style.display = (newState === VoiceState.IDLE && lastResponseText) ? 'flex' : 'none';
        voiceSpeedControls.style.display = newState === VoiceState.SPEAKING ? 'flex' : 'none';

        // Main button label
        if (newState === VoiceState.IDLE) {
            voiceMainBtn.title = t('voice_idle');
        } else {
            voiceMainBtn.title = 'End Voice Mode';
        }
    }

    // --- Web Audio API: VAD ---
    async function startAudioCapture() {
        try {
            micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(micStream);
            analyserNode = audioContext.createAnalyser();
            analyserNode.fftSize = 512;
            analyserNode.smoothingTimeConstant = 0.3;
            source.connect(analyserNode);
            // Noise calibration for first second
            isCalibrating = true;
            noiseFloor = 0.01;
            let calSamples = 0, calSum = 0;
            const calStartTime = Date.now();
            const calInterval = setInterval(() => {
                const data = new Uint8Array(analyserNode.frequencyBinCount);
                analyserNode.getByteTimeDomainData(data);
                let rms = 0;
                for (let i = 0; i < data.length; i++) { const v = (data[i] - 128) / 128; rms += v * v; }
                rms = Math.sqrt(rms / data.length);
                calSum += rms; calSamples++;
                if (Date.now() - calStartTime > VOICE_CONFIG.NOISE_CALIBRATION_MS) {
                    clearInterval(calInterval);
                    noiseFloor = Math.max(0.005, (calSum / calSamples) * VOICE_CONFIG.SPEECH_THRESHOLD_MULTIPLIER);
                    isCalibrating = false;
                    logVoice('Noise floor calibrated: ' + noiseFloor.toFixed(4));
                }
            }, 50);
            startVADLoop();
            return true;
        } catch (e) {
            logVoice('Mic error: ' + e.message);
            setVoiceState(VoiceState.IDLE);
            voiceStateText.textContent = t('voice_error');
            return false;
        }
    }

    function startVADLoop() {
        const dataArr = new Uint8Array(analyserNode.frequencyBinCount);
        let speechFrameCount = 0;
        let silenceFrameCount = 0;
        const FRAME_MS = 30;
        const SPEECH_FRAMES = Math.ceil(VOICE_CONFIG.MIN_SPEECH_DURATION_MS / FRAME_MS);
        const SILENCE_FRAMES = Math.ceil(VOICE_CONFIG.MIN_SILENCE_DURATION_MS / FRAME_MS);

        function tick() {
            if (!voiceActive) return;
            analyserNode.getByteTimeDomainData(dataArr);
            let rms = 0;
            for (let i = 0; i < dataArr.length; i++) { const v = (dataArr[i] - 128) / 128; rms += v * v; }
            rms = Math.sqrt(rms / dataArr.length);
            // Update meter
            const pct = Math.min(100, Math.round((rms / Math.max(noiseFloor * 3, 0.1)) * 100));
            voiceMeterFill.style.width = pct + '%';

            const isSpeech = rms > noiseFloor;
            // Barge-in detection: if speaking and user starts talking
            if (voiceState === VoiceState.SPEAKING && isSpeech && speechFrameCount >= SPEECH_FRAMES * 2) {
                handleBargeIn();
                speechFrameCount = 0;
            }
            if (isSpeech) {
                speechFrameCount++;
                silenceFrameCount = 0;
                if (voiceState === VoiceState.LISTENING && speechFrameCount >= SPEECH_FRAMES) {
                    setVoiceState(VoiceState.USER_SPEAKING);
                    speechStart = Date.now();
                    clearSilenceTimer();
                } else if (voiceState === VoiceState.USER_PAUSED && speechFrameCount >= SPEECH_FRAMES) {
                    // User resumed speaking after pause
                    setVoiceState(VoiceState.USER_SPEAKING);
                    clearSilenceTimer();
                }
            } else {
                silenceFrameCount++;
                if (voiceState === VoiceState.USER_SPEAKING && silenceFrameCount >= SILENCE_FRAMES) {
                    setVoiceState(VoiceState.USER_PAUSED);
                    startSilenceTimer();
                }
                speechFrameCount = 0;
            }
            vadAnimFrame = requestAnimationFrame(tick);
        }
        vadAnimFrame = requestAnimationFrame(tick);
    }

    function stopAudioCapture() {
        if (vadAnimFrame) { cancelAnimationFrame(vadAnimFrame); vadAnimFrame = null; }
        if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
        if (audioContext) { audioContext.close().catch(()=>{}); audioContext = null; analyserNode = null; }
        voiceMeterFill.style.width = '0%';
    }

    // --- Silence / Pause Detection ---
    function clearSilenceTimer() { silenceTimers.forEach(t => clearTimeout(t)); silenceTimers = []; }

    function startSilenceTimer() {
        silenceStart = Date.now();
        clearSilenceTimer();
        const transcriptWordCount = (finalTranscript + ' ' + interimTranscript).trim().split(/\s+/).filter(w => w).length;
        const isShort = transcriptWordCount < VOICE_CONFIG.SHORT_TRANSCRIPT_WORDS;
        const finalizeMs = isShort ? VOICE_CONFIG.SILENCE_SHORT_TRANSCRIPT_MS : VOICE_CONFIG.SILENCE_LONG_MS;

        // Stage 0: Under SILENCE_IGNORE_MS — just continue, no feedback change
        // Stage 1: At SILENCE_IGNORE_MS (1200ms) — show "take your time" (continue indicator)
        silenceTimers.push(setTimeout(() => {
            if (voiceState === VoiceState.USER_PAUSED) {
                voiceStateText.textContent = t('voice_take_your_time');
            }
        }, VOICE_CONFIG.SILENCE_IGNORE_MS));

        // Stage 2: At SILENCE_THINKING_MS (4000ms) — thinking pause indicator
        silenceTimers.push(setTimeout(() => {
            if (voiceState === VoiceState.USER_PAUSED) {
                voiceStateText.textContent = t('voice_thinking');
            }
        }, VOICE_CONFIG.SILENCE_THINKING_MS));

        // Stage 3: Finalize at SILENCE_LONG_MS (7000ms) or longer for short transcripts
        silenceTimers.push(setTimeout(() => {
            if (voiceState === VoiceState.USER_PAUSED) {
                finalizeTranscript();
            }
        }, finalizeMs));
    }

    function checkImmediateFinalize(text) {
        const lower = text.toLowerCase().trim();
        return VOICE_CONFIG.IMMEDIATE_FINALIZE_PHRASES.some(p => lower.includes(p));
    }

    // --- Speech Recognition ---
    function initRecognition() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
            logVoice('SpeechRecognition not supported');
            return null;
        }
        const rec = new SR();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = currentLanguage === 'bn_bd' ? 'bn-BD' : 'en-US';
        rec.maxAlternatives = 1;

        rec.onresult = (event) => {
            let interim = '';
            let final = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    final += transcript;
                } else {
                    interim += transcript;
                }
            }
            if (final) {
                finalTranscript = (finalTranscript + ' ' + final).trim();
                // Check immediate finalize
                if (checkImmediateFinalize(final)) {
                    finalizeTranscript();
                    return;
                }
            }
            interimTranscript = interim;
            const display = (finalTranscript + ' ' + interimTranscript).trim();
            voiceTranscriptText.textContent = display || t('voice_listening');
            // If we get interim results while in paused state, user is speaking again
            if (interim && voiceState === VoiceState.USER_PAUSED) {
                clearSilenceTimer();
                setVoiceState(VoiceState.USER_SPEAKING);
            }
        };
        rec.onerror = (e) => {
            logVoice('Recognition error: ' + e.error);
            if (e.error === 'not-allowed' || e.error === 'no-speech') {
                if (voiceActive) {
                    // Try restart
                    setTimeout(() => { if (voiceActive) startRecognition(); }, 500);
                }
            }
        };
        rec.onend = () => {
            recognitionActive = false;
            logVoice('Recognition ended');
            // Auto-restart if still active
            if (voiceActive && voiceState !== VoiceState.PROCESSING && voiceState !== VoiceState.SPEAKING) {
                setTimeout(() => { if (voiceActive) startRecognition(); }, 300);
            }
        };
        return rec;
    }

    function startRecognition() {
        if (!recognition) recognition = initRecognition();
        if (!recognition) {
            voiceTranscriptText.textContent = 'Live transcript is not supported in this browser. Recording still works if backend STT is connected.';
            return false;
        }
        try {
            recognition.lang = currentLanguage === 'bn_bd' ? 'bn-BD' : 'en-US';
            recognition.start();
            recognitionActive = true;
            logVoice('Recognition started');
            return true;
        } catch (e) {
            logVoice('Recognition start error: ' + e.message);
            return false;
        }
    }

    function stopRecognition() {
        if (recognition && recognitionActive) {
            try { recognition.stop(); } catch(e) {}
            recognitionActive = false;
        }
    }

    // --- Finalize & Send ---
    async function finalizeTranscript() {
        clearSilenceTimer();

        // Backend STT flow: stop recording and upload audio
        if (activeVoiceEngine === 'backend' && backendSTTAvailable) {
            setVoiceState(VoiceState.FINALIZING);
            logVoice('Finalizing with backend STT...');
            stopBackendRecording();
            // The onstop handler of MediaRecorder will call sendAudioToBackendSTT
            // which will then call sendVoiceMessage with the transcript
            return;
        }

        // Browser STT flow: use SpeechRecognition transcript
        const transcript = (finalTranscript + ' ' + interimTranscript).trim();
        if (!transcript) {
            logVoice('Empty transcript, returning to listening');
            setVoiceState(VoiceState.LISTENING);
            return;
        }
        setVoiceState(VoiceState.FINALIZING);
        voiceTranscriptText.textContent = transcript;
        await new Promise(r => setTimeout(r, 300));
        setVoiceState(VoiceState.PROCESSING);
        logVoice('Final transcript (' + transcript.split(/\s+/).length + ' words): ' + transcript);
        await sendVoiceMessage(transcript);
    }

    // --- Backend Integration ---
    async function sendVoiceMessage(transcript) {
        // Show "I heard..." for low confidence / short transcripts
        const wordCount = transcript.split(/\s+/).length;
        if (wordCount < 3) {
            voiceStateText.textContent = t('voice_i_heard') + ' "' + transcript + '" \u2014 ' + t('voice_repeat');
        }
    
        // Check backend availability
        if (!backendAvailable) {
            const isHealthy = await checkBackendHealth();
            if (!isHealthy) {
                logVoice('Backend offline, cannot send transcript');
                voiceStateText.textContent = currentLanguage === 'bn_bd'
                    ? '\u09ac\u09cd\u09af\u09be\u0995\u098f\u0982\u09a1 \u0985\u09ab\u09b2\u09be\u0987\u09a8\u0964 \u0986\u09ac\u09be\u09b0 \u099a\u09c7\u09b7\u09cd\u099f\u09be \u0995\u09b0\u09c1\u09a8\u0964'
                    : 'Backend is offline. Please check connection.';
                setTimeout(() => { if (voiceActive) setVoiceState(VoiceState.LISTENING); }, 3000);
                return;
            }
        }
    
        // Step 1: Save transcript via /api/voice/transcript
        try {
            await fetch('/api/voice/transcript', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: transcript,
                    session_id: companionSessionId || '',
                    language: currentLanguage
                })
            });
        } catch (e) {
            logVoice('Transcript save failed: ' + e.message);
            // Continue to chat anyway
        }
    
        // Step 2: Get response via /api/chat
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: transcript,
                    session_id: companionSessionId || '',
                    language: currentLanguage,
                    input_mode: 'voice',
                    mode: currentMode
                })
            });
            const result = await res.json();
            let responseText = '';
            if (result.response) {
                responseText = result.response;
            } else if (result.assistant_message) {
                responseText = result.assistant_message.response_text || result.assistant_message.response || '';
            }
            // Update mode from backend response
            if (result.metadata && result.metadata.resolved_mode && result.metadata.resolved_mode !== currentMode) {
                if (result.metadata.resolved_mode === 'safety') {
                    currentMode = 'safety';
                    updateModeSelector();
                    updateProfileForMode();
                } else {
                    setAgentMode(result.metadata.resolved_mode);
                }
            }
            if (!responseText) {
                responseText = currentLanguage === 'bn_bd'
                    ? '\u09a6\u09c1\u0983\u0996\u09bf\u09a4, \u0986\u09ae\u09bf \u098f\u0996\u09a8 \u09b8\u09be\u09b9\u09be\u09af\u09cd\u09af \u0995\u09b0\u09a4\u09c7 \u09aa\u09be\u09b0\u099b\u09bf \u09a8\u09be\u0964'
                    : 'Sorry, I couldn\'t process that.';
            }
            lastResponseText = responseText;
            // Add to chat
            appendMessage('user', transcript);
            appendMessage('assistant', responseText);
            // Show in voice panel
            voiceResponseText.textContent = responseText;
            voiceResponseText.style.display = 'block';
            // Speak if enabled
            const readAloud = document.getElementById('speakResponseToggle').checked;
            if (readAloud) {
                speakResponse(responseText);
            } else {
                // Go back to listening
                setTimeout(() => {
                    if (voiceActive) setVoiceState(VoiceState.LISTENING);
                    else setVoiceState(VoiceState.IDLE);
                }, 500);
            }
        } catch (e) {
            logVoice('Backend error: ' + e.message);
            // Retry once after short delay
            try {
                const retryRes = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: transcript,
                        session_id: companionSessionId || '',
                        language: currentLanguage,
                        input_mode: 'voice',
                        mode: currentMode
                    })
                });
                const retryResult = await retryRes.json();
                const responseText = retryResult.response || (currentLanguage === 'bn_bd'
                    ? '\u09a6\u09c1\u0983\u0996\u09bf\u09a4, \u0986\u09ae\u09bf \u098f\u0996\u09a8 \u09b8\u09be\u09b9\u09be\u09af\u09cd\u09af \u0995\u09b0\u09a4\u09c7 \u09aa\u09be\u09b0\u099b\u09bf \u09a8\u09be\u0964'
                    : 'Sorry, I couldn\'t process that.');
                lastResponseText = responseText;
                appendMessage('user', transcript);
                appendMessage('assistant', responseText);
                voiceResponseText.textContent = responseText;
                voiceResponseText.style.display = 'block';
                const readAloud = document.getElementById('speakResponseToggle').checked;
                if (readAloud) {
                    speakResponse(responseText);
                } else {
                    setTimeout(() => { if (voiceActive) setVoiceState(VoiceState.LISTENING); else setVoiceState(VoiceState.IDLE); }, 500);
                }
            } catch (retryErr) {
                logVoice('Retry also failed: ' + retryErr.message);
                voiceStateText.textContent = currentLanguage === 'bn_bd'
                    ? '\u09b8\u0982\u09af\u09cb\u0997 \u09a4\u09cd\u09b0\u09c1\u099f\u09bf\u0964 \u0986\u09ac\u09be\u09b0 \u099a\u09c7\u09b7\u09cd\u099f\u09be \u0995\u09b0\u09c1\u09a8\u0964'
                    : 'Connection error. Trying again...';
                backendAvailable = false;
                setTimeout(() => { if (voiceActive) setVoiceState(VoiceState.LISTENING); }, 3000);
            }
        }
    }

    // --- Speech Synthesis (Browser TTS + Backend TTS) ---
    async function speakResponse(text) {
        // Try backend TTS first if active engine is backend
        if (activeVoiceEngine === 'backend' && backendTTSAvailable) {
            const success = await speakResponseBackend(text);
            if (success) return;
            // Backend TTS failed, fallback to browser
            logVoice('Backend TTS failed, falling back to browser');
        }

        // Browser TTS fallback
        if (!window.speechSynthesis) {
            logVoice('SpeechSynthesis not available');
            setVoiceState(VoiceState.IDLE);
            return;
        }
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        synthUtterance = new SpeechSynthesisUtterance(text);
        synthUtterance.lang = currentLanguage === 'bn_bd' ? 'bn-BD' : 'en-US';
        synthUtterance.rate = getEffectiveSpeed();
        synthUtterance.volume = getEffectiveVolume();
        // Try to pick a female voice
        const voices = window.speechSynthesis.getVoices();
        if (voices.length) {
            const preferred = voices.find(v => v.lang.startsWith(synthUtterance.lang.substring(0,2)) && /female|woman|zira|samantha|google.*female/i.test(v.name))
                || voices.find(v => v.lang.startsWith(synthUtterance.lang.substring(0,2)))
                || voices[0];
            if (preferred) synthUtterance.voice = preferred;
        }
        synthUtterance.onstart = () => {
            setVoiceState(VoiceState.SPEAKING);
            synthPaused = false;
            // Arm backend EchoGuard
            if (backendAvailable) {
                fetch('/api/voice/playback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'speak', text: text, language: currentLanguage })
                }).catch(() => {});
            }
        };
        synthUtterance.onend = () => {
            synthUtterance = null;
            synthPaused = false;
            voicePauseBtn.style.display = 'none';
            voiceResumeBtn.style.display = 'none';
            // Disarm backend EchoGuard
            if (backendAvailable) {
                fetch('/api/voice/playback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'stop' })
                }).catch(() => {});
            }
            if (voiceActive) {
                setVoiceState(VoiceState.LISTENING);
                // Reset transcript for next turn
                finalTranscript = '';
                interimTranscript = '';
                voiceTranscriptText.textContent = '';
            } else {
                setVoiceState(VoiceState.IDLE);
            }
        };
        synthUtterance.onerror = () => {
            synthUtterance = null;
            if (voiceActive) setVoiceState(VoiceState.LISTENING);
        };
        window.speechSynthesis.speak(synthUtterance);
    }

    function stopSpeaking() {
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        synthUtterance = null;
        synthPaused = false;
        voicePauseBtn.style.display = 'none';
        voiceResumeBtn.style.display = 'none';
        // Stop backend audio if playing
        stopBackendAudio();
        // Notify backend to disarm EchoGuard
        if (backendAvailable) {
            fetch('/api/voice/playback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'stop' })
            }).catch(() => {});
        }
    }

    // --- Barge-In (Interrupt ZARA while speaking) ---
    function handleBargeIn() {
        if (voiceState === VoiceState.SPEAKING && voiceActive) {
            const bargeInEnabled = voiceBargeInToggle ? voiceBargeInToggle.checked : true;
            if (bargeInEnabled) {
                logVoice('Barge-in detected');
                stopSpeaking();
                voiceStateText.textContent = t('voice_interrupted');
                setVoiceState(VoiceState.USER_SPEAKING);
                finalTranscript = '';
                interimTranscript = '';
                voiceTranscriptText.textContent = '';
                // Notify backend to disarm EchoGuard
                if (backendAvailable) {
                    fetch('/api/voice/playback', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'stop' })
                    }).catch(() => {});
                }
            }
        }
    }

    // --- Start / Stop Voice Mode ---
    async function startVoiceMode() {
        voiceActive = true;
        finalTranscript = '';
        interimTranscript = '';
        lastResponseText = '';
        voiceResponseText.style.display = 'none';
        voiceResponseText.textContent = '';
        setVoiceState(VoiceState.LISTENING);
        voiceTranscriptText.textContent = t('voice_listening');

        // Check backend health before starting
        const isHealthy = await checkBackendHealth();
        if (!isHealthy) {
            logVoice('Backend offline at voice mode start');
            voiceStateText.textContent = currentLanguage === 'bn_bd'
                ? '\u09ac\u09cd\u09af\u09be\u0995\u098f\u0982\u09a1 \u0985\u09ab\u09b2\u09be\u0987\u09a8\u0964 \u0986\u09ac\u09be\u09b0 \u099a\u09c7\u09b7\u09cd\u099f\u09be \u0995\u09b0\u09c1\u09a8\u0964'
                : 'Backend is offline. Voice mode needs the backend.';
        }

        // Start backend health monitor
        startBackendHealthMonitor();

        // Detect backend voice engines
        await detectBackendVoiceEngines();

        const audioOk = await startAudioCapture();
        if (audioOk) {
            if (activeVoiceEngine === 'backend' && backendSTTAvailable) {
                // Use backend STT: record audio with MediaRecorder
                startBackendRecording();
                logVoice('Using backend STT (MediaRecorder)');
            } else {
                // Use browser SpeechRecognition
                startRecognition();
                logVoice('Using browser SpeechRecognition');
            }
        } else {
            // Mic denied
            voiceStateText.textContent = t('voice_error');
            voiceActive = false;
            setVoiceState(VoiceState.IDLE);
        }
    }

    function stopVoiceMode() {
        voiceActive = false;
        clearSilenceTimer();
        stopRecognition();
        stopAudioCapture();
        stopSpeaking();
        stopBackendAudio();
        stopBackendRecording();
        stopBackendHealthMonitor();
        setVoiceState(VoiceState.IDLE);
        voiceTranscriptText.textContent = '';
        voiceResponseText.style.display = 'none';
        voiceTranscript.style.display = 'none';
        finalTranscript = '';
        interimTranscript = '';
    }

    // --- Button Handlers ---
    // Main button: Start / End voice mode
    voiceMainBtn.addEventListener('click', () => {
        if (voiceState === VoiceState.IDLE) {
            startVoiceMode();
        } else {
            stopVoiceMode();
        }
    });

    // Stop button: finalize current transcript or stop
    voiceStopBtn.addEventListener('click', () => {
        if (voiceState === VoiceState.SPEAKING) {
            stopSpeaking();
            if (voiceActive) setVoiceState(VoiceState.LISTENING);
        } else if ([VoiceState.LISTENING, VoiceState.USER_SPEAKING, VoiceState.USER_PAUSED].includes(voiceState)) {
            stopRecognition();
            finalizeTranscript();
        } else {
            stopVoiceMode();
        }
    });

    // Pause TTS
    voicePauseBtn.addEventListener('click', () => {
        if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
            window.speechSynthesis.pause();
            synthPaused = true;
            voicePauseBtn.style.display = 'none';
            voiceResumeBtn.style.display = 'flex';
            voiceStateText.textContent = t('voice_paused');
        }
    });

    // Resume TTS
    voiceResumeBtn.addEventListener('click', () => {
        if (window.speechSynthesis.paused) {
            window.speechSynthesis.resume();
            synthPaused = false;
            voiceResumeBtn.style.display = 'none';
            voicePauseBtn.style.display = 'flex';
            voiceStateText.textContent = t('voice_speaking');
        }
    });

    // Replay last response
    voiceReplayBtn.addEventListener('click', async () => {
        if (lastResponseText) {
            if (activeVoiceEngine === 'backend' && backendTTSAvailable) {
                const success = await speakResponseBackend(lastResponseText);
                if (success) return;
            }
            speakResponse(lastResponseText);
        }
    });

    // Settings toggles
    if (voiceSettingsToggle) {
        voiceSettingsToggle.addEventListener('click', () => {
            const panel = voiceSettingsPanel;
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        });
    }

    // Voice engine selector
    const voiceEngineSelect = document.getElementById('voiceEngineSelect');
    if (voiceEngineSelect) {
        // Restore saved preference
        const savedEngine = localStorage.getItem('zaraVoiceEngine');
        if (savedEngine) {
            voiceEngineSelect.value = savedEngine;
            voiceEngineMode = savedEngine;
        }
        voiceEngineSelect.addEventListener('change', () => {
            voiceEngineMode = voiceEngineSelect.value;
            localStorage.setItem('zaraVoiceEngine', voiceEngineMode);
            resolveActiveEngine();
            logVoice('Voice engine changed to: ' + voiceEngineMode);
        });
    }

    // Voice profile selector
    if (voiceProfileSelect) {
        // Restore saved preference
        const savedProfile = localStorage.getItem('zaraVoiceProfile');
        if (savedProfile && voiceProfileDescriptions[savedProfile]) {
            voiceProfileSelect.value = savedProfile;
            currentVoiceProfile = savedProfile;
        }
        // Show initial description
        updateProfileDescription();

        voiceProfileSelect.addEventListener('change', () => {
            currentVoiceProfile = voiceProfileSelect.value;
            localStorage.setItem('zaraVoiceProfile', currentVoiceProfile);
            updateProfileDescription();
            logVoice('Voice profile changed to: ' + currentVoiceProfile);
        });
    }

    // Auto emotional voice toggle
    if (voiceAutoEmotionalToggle) {
        const savedAuto = localStorage.getItem('zaraAutoVoice');
        if (savedAuto !== null) {
            autoEmotionalVoice = savedAuto !== 'false';
            voiceAutoEmotionalToggle.checked = autoEmotionalVoice;
        }
        voiceAutoEmotionalToggle.addEventListener('change', () => {
            autoEmotionalVoice = voiceAutoEmotionalToggle.checked;
            localStorage.setItem('zaraAutoVoice', String(autoEmotionalVoice));
            logVoice('Auto emotional voice: ' + (autoEmotionalVoice ? 'on' : 'off'));
        });
    }

    // --- Voice Volume & Speed Setting Sliders ---
    const voiceVolumeSetting = document.getElementById('voiceVolumeSetting');
    const voiceVolumeValue = document.getElementById('voiceVolumeValue');
    const voiceSpeedSetting = document.getElementById('voiceSpeedSetting');
    const voiceSpeedValue = document.getElementById('voiceSpeedValue');
    const nightVoiceStatus = document.getElementById('nightVoiceStatus');

    // Restore saved values
    const savedVol = localStorage.getItem('zaraVoiceVolume');
    if (savedVol && voiceVolumeSetting) voiceVolumeSetting.value = savedVol;
    const savedSpd = localStorage.getItem('zaraVoiceSpeed');
    if (savedSpd && voiceSpeedSetting) voiceSpeedSetting.value = savedSpd;

    function updateVolumeDisplay() {
        if (voiceVolumeValue) {
            const effective = getEffectiveVolume();
            voiceVolumeValue.textContent = Math.round(effective * 100) + '%';
        }
    }
    function updateSpeedDisplay() {
        if (voiceSpeedValue) {
            const effective = getEffectiveSpeed();
            voiceSpeedValue.textContent = effective.toFixed(1) + 'x';
        }
    }

    if (voiceVolumeSetting) {
        voiceVolumeSetting.addEventListener('input', () => {
            localStorage.setItem('zaraVoiceVolume', voiceVolumeSetting.value);
            updateVolumeDisplay();
        });
        updateVolumeDisplay();
    }
    if (voiceSpeedSetting) {
        voiceSpeedSetting.addEventListener('input', () => {
            localStorage.setItem('zaraVoiceSpeed', voiceSpeedSetting.value);
            updateSpeedDisplay();
        });
        updateSpeedDisplay();
    }

    // Update night voice status visibility
    function updateNightVoiceStatus() {
        if (nightVoiceStatus) {
            nightVoiceStatus.style.display = nightModeActive ? 'flex' : 'none';
        }
        updateVolumeDisplay();
        updateSpeedDisplay();
    }
    updateNightVoiceStatus();

    function updateProfileDescription() {
        if (voiceProfileDesc) {
            voiceProfileDesc.textContent = voiceProfileDescriptions[currentVoiceProfile] || '';
        }
    }

    // Speaking indicator helpers
    function showSpeakingIndicator(style, text) {
        if (!voiceSpeakingIndicator) return;
        voiceSpeakingIndicator.style.display = 'flex';
        if (speakingStatusText) {
            speakingStatusText.textContent = styleStatusMessages[style] || 'Zara is speaking...';
        }
        if (speakingSentenceText && text) {
            // Show first sentence as preview
            const firstSentence = text.split(/[.!?]/)[0].trim();
            speakingSentenceText.textContent = firstSentence.length > 80 ? firstSentence.slice(0, 80) + '...' : firstSentence;
        }
    }

    function hideSpeakingIndicator() {
        if (voiceSpeakingIndicator) voiceSpeakingIndicator.style.display = 'none';
        if (speakingStatusText) speakingStatusText.textContent = '';
        if (speakingSentenceText) speakingSentenceText.textContent = '';
    }

    // Voice preview button
    if (voicePreviewBtn) {
        voicePreviewBtn.addEventListener('click', async () => {
            // Use selected preview sample
            const sampleKey = voicePreviewSample ? voicePreviewSample.value : 'supportive';
            const previewText = previewSampleTexts[sampleKey] || "Hi, I'm Zara. I'm here with you.";
            voicePreviewBtn.disabled = true;
            if (voicePreviewStatus) voicePreviewStatus.textContent = 'Playing...';

            // Try backend TTS first
            if (backendTTSAvailable) {
                try {
                    const res = await fetch('/api/voice/tts', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            text: previewText,
                            voice: 'female',
                            voice_profile: currentVoiceProfile,
                            language: 'en',
                            speed: getEffectiveSpeed(),
                            volume: getEffectiveVolume(),
                            night_mode: nightModeActive
                        })
                    });
                    if (res.ok) {
                        const contentType = res.headers.get('content-type') || '';
                        if (contentType.includes('audio')) {
                            const audioUrl = URL.createObjectURL(await res.blob());
                            const previewAudio = new Audio(audioUrl);
                            const appliedVol = res.headers.get('X-Zara-Applied-Volume');
                            previewAudio.volume = appliedVol ? parseFloat(appliedVol) : getEffectiveVolume();
                            previewAudio.onended = () => {
                                URL.revokeObjectURL(audioUrl);
                                voicePreviewBtn.disabled = false;
                                if (voicePreviewStatus) voicePreviewStatus.textContent = '';
                            };
                            previewAudio.onerror = () => {
                                URL.revokeObjectURL(audioUrl);
                                voicePreviewBtn.disabled = false;
                                if (voicePreviewStatus) voicePreviewStatus.textContent = 'Playback error';
                            };
                            await previewAudio.play();
                            return;
                        }
                    }
                } catch (e) {
                    logVoice('Preview backend TTS failed: ' + e.message);
                }
            }

            // Fallback to browser TTS
            if (window.speechSynthesis) {
                window.speechSynthesis.cancel();
                const utt = new SpeechSynthesisUtterance(previewText);
                utt.lang = 'en-US';
                utt.rate = 0.95;
                const voices = window.speechSynthesis.getVoices();
                if (voices.length) {
                    const preferred = voices.find(v => /female|woman|zira|samantha/i.test(v.name) && v.lang.startsWith('en'))
                        || voices.find(v => v.lang.startsWith('en'))
                        || voices[0];
                    if (preferred) utt.voice = preferred;
                }
                utt.onend = () => {
                    voicePreviewBtn.disabled = false;
                    if (voicePreviewStatus) voicePreviewStatus.textContent = '';
                };
                utt.onerror = () => {
                    voicePreviewBtn.disabled = false;
                    if (voicePreviewStatus) voicePreviewStatus.textContent = 'Playback error';
                };
                window.speechSynthesis.speak(utt);
                return;
            }

            // No TTS available
            voicePreviewBtn.disabled = false;
            if (voicePreviewStatus) voicePreviewStatus.textContent = 'No TTS available';
        });
    }

    // Playback speed
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const speed = parseFloat(btn.dataset.speed);
            if (synthUtterance) {
                // Restart speech at new speed
                const text = lastResponseText;
                stopSpeaking();
                if (text) {
                    synthUtterance = new SpeechSynthesisUtterance(text);
                    synthUtterance.rate = speed;
                    synthUtterance.lang = currentLanguage === 'bn_bd' ? 'bn-BD' : 'en-US';
                    synthUtterance.onstart = () => setVoiceState(VoiceState.SPEAKING);
                    synthUtterance.onend = () => {
                        synthUtterance = null;
                        if (voiceActive) { setVoiceState(VoiceState.LISTENING); finalTranscript=''; interimTranscript=''; voiceTranscriptText.textContent=''; }
                        else setVoiceState(VoiceState.IDLE);
                    };
                    window.speechSynthesis.speak(synthUtterance);
                }
            }
        });
    });

    // Volume slider
    if (voiceVolumeSlider) {
        voiceVolumeSlider.addEventListener('input', () => {
            // Volume for SpeechSynthesis
            const vol = parseInt(voiceVolumeSlider.value) / 100;
            if (synthUtterance) synthUtterance.volume = vol;
        });
    }

    // Clean up when leaving voice view
    document.getElementById('voiceCloseBtn').addEventListener('click', () => {
        stopVoiceMode();
        showView('assistant');
    });

    // Chat mic button -> enter voice mode and start listening
    chatMicBtn.addEventListener('click', () => { showView('voice'); if (voiceState === VoiceState.IDLE) startVoiceMode(); });

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
            if (btn.dataset.section === 'adv-timeline') initTimeline();
            if (btn.dataset.section === 'adv-health') initHealthPage();
            if (btn.dataset.section === 'adv-workspace') initWorkspace();
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
            item.innerHTML  = `<div class="thought-time">${timeStr}</div><strong>${t(tmpl.label)}:</strong> ${tmpl.content}`;
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

    // Auto-init session + system status check
    (async function initSession() {
        // Check backend health on startup
        await checkBackendHealth();
        try {
            const res = await fetch('/api/system/status');
            const data = await res.json();
            if (data && data.orchestrator) {
                logVoice('System status: ' + JSON.stringify(data.orchestrator));
            }
        } catch (e) { logVoice('System status check failed (backend may be offline).'); }
        try {
            const res = await fetch('/api/session/current');
            const data = await res.json();
            if (data && data.session_id) {
                companionSessionId = data.session_id;
                companionSessionActive = true;
            }
        } catch (e) { console.log('No existing session, will create on first message.'); }
    })();

    // ===== Connected Backend APIs =====
    // GET  /api/health           — backend health check (used on init + voice mode start + 15s interval)
    // GET  /api/system/status    — system status on init
    // POST /api/voice/transcript — save finalized transcript
    // POST /api/voice/state      — sync frontend voice state to backend
    // POST /api/voice/playback   — arm/disarm EchoGuard around TTS
    // POST /api/chat             — get ZARA response via Orchestrator

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

    // ===== TIMELINE (Episodic Memory) =====
    let _timelineInitialized = false;
    let _timelineSearchTimer = null;

    function initTimeline() {
        if (_timelineInitialized) return;
        _timelineInitialized = true;

        // Period tab clicks
        document.querySelectorAll('#timelinePeriodTabs .period-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('#timelinePeriodTabs .period-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                loadTimeline(tab.dataset.period || 'today');
            });
        });

        // Search input with debounce
        const searchInput = document.getElementById('timelineSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(_timelineSearchTimer);
                _timelineSearchTimer = setTimeout(() => {
                    const q = searchInput.value.trim();
                    if (q.length >= 2) {
                        loadTimelineSearch(q);
                    } else {
                        loadTimeline('today');
                    }
                }, 300);
            });
        }

        loadTimeline('today');
        loadTimelineProjects();
        loadTimelineEmotions();
    }

    function loadTimeline(period) {
        const listEl = document.getElementById('timelineEpisodesList');
        if (!listEl) return;
        const t = translations[currentLang] || translations.en;
        listEl.innerHTML = '<div class="empty-state">' + (t['timeline_loading'] || 'Loading...') + '</div>';

        fetch('/api/episodes/timeline')
            .then(r => r.json())
            .then(data => {
                if (!data.success) { listEl.innerHTML = '<div class="empty-state">Timeline unavailable</div>'; return; }
                const episodes = data[period] || [];
                if (episodes.length === 0) {
                    listEl.innerHTML = '<div class="empty-state">' + (t['timeline_no_episodes'] || 'No episodes') + '</div>';
                    return;
                }
                listEl.innerHTML = '';
                episodes.forEach(ep => listEl.appendChild(renderEpisodeCard(ep)));

                // Also populate achievements and pending from the same response
                const achList = document.getElementById('timelineAchievementsList');
                if (achList && data.achievements) {
                    achList.innerHTML = '';
                    if (data.achievements.length === 0) {
                        achList.innerHTML = '<div class="empty-state">' + (t['timeline_no_episodes'] || 'None') + '</div>';
                    } else {
                        data.achievements.forEach(ep => achList.appendChild(renderEpisodeCard(ep)));
                    }
                }
                const pendList = document.getElementById('timelinePendingList');
                if (pendList && data.pending) {
                    pendList.innerHTML = '';
                    if (data.pending.length === 0) {
                        pendList.innerHTML = '<div class="empty-state">' + (t['timeline_no_episodes'] || 'None') + '</div>';
                    } else {
                        data.pending.forEach(ep => pendList.appendChild(renderEpisodeCard(ep)));
                    }
                }
            })
            .catch(() => { listEl.innerHTML = '<div class="empty-state">Timeline unavailable</div>'; });
    }

    function renderEpisodeCard(ep) {
        const card = document.createElement('div');
        card.className = 'episode-card';

        const emotion = (ep.emotion || 'neutral').toLowerCase();
        const importancePct = Math.round((ep.importance || 0) * 100);
        const dateStr = ep.started_at ? new Date(ep.started_at).toLocaleDateString() : '';

        let topicsHtml = '';
        if (ep.topics && ep.topics.length > 0) {
            topicsHtml = '<div class="episode-topics">' +
                ep.topics.map(t => '<span class="episode-topic-tag">' + t + '</span>').join('') + '</div>';
        }

        let pendingHtml = '';
        if (ep.pending_tasks && ep.pending_tasks.length > 0) {
            pendingHtml = '<div class="episode-pending">Pending: ' + ep.pending_tasks.join(', ') + '</div>';
        }

        card.innerHTML =
            '<div class="episode-card-header">' +
                '<span class="episode-title">' + (ep.title || 'Untitled') + '</span>' +
                '<span class="episode-date">' + dateStr + '</span>' +
            '</div>' +
            '<div class="episode-summary">' + (ep.summary || '') + '</div>' +
            '<div class="episode-meta">' +
                '<span class="emotion-badge ' + emotion + '">' + emotion + '</span>' +
            '</div>' +
            '<div class="importance-bar"><div class="importance-bar-fill" style="width:' + importancePct + '%"></div></div>' +
            topicsHtml + pendingHtml;

        return card;
    }

    function loadTimelineProjects() {
        const listEl = document.getElementById('timelineProjectsList');
        if (!listEl) return;
        const t = translations[currentLang] || translations.en;

        fetch('/api/episodes/projects')
            .then(r => r.json())
            .then(data => {
                if (!data.success || !data.projects) { listEl.innerHTML = '<div class="empty-state">Unavailable</div>'; return; }
                const keys = Object.keys(data.projects);
                if (keys.length === 0) {
                    listEl.innerHTML = '<div class="empty-state">' + (t['timeline_no_episodes'] || 'None') + '</div>';
                    return;
                }
                listEl.innerHTML = '';
                keys.forEach(topic => {
                    const group = document.createElement('div');
                    group.className = 'project-group';
                    group.innerHTML = '<div class="project-group-title">' + topic + '</div>';
                    data.projects[topic].forEach(ep => group.appendChild(renderEpisodeCard(ep)));
                    listEl.appendChild(group);
                });
            })
            .catch(() => { listEl.innerHTML = '<div class="empty-state">Unavailable</div>'; });
    }

    function loadTimelineEmotions() {
        const listEl = document.getElementById('timelineEmotionList');
        if (!listEl) return;
        const t = translations[currentLang] || translations.en;

        fetch('/api/episodes/emotions')
            .then(r => r.json())
            .then(data => {
                if (!data.success || !data.journey) { listEl.innerHTML = '<div class="empty-state">Unavailable</div>'; return; }
                if (data.journey.length === 0) {
                    listEl.innerHTML = '<div class="empty-state">' + (t['timeline_no_episodes'] || 'None') + '</div>';
                    return;
                }
                listEl.innerHTML = '';
                data.journey.forEach(snap => {
                    const card = document.createElement('div');
                    card.className = 'episode-card';
                    const emotion = (snap.emotion || 'neutral').toLowerCase();
                    const intensityPct = Math.round((snap.intensity || 0) * 100);
                    const dateStr = snap.timestamp ? new Date(snap.timestamp).toLocaleDateString() : '';
                    card.innerHTML =
                        '<div class="episode-card-header">' +
                            '<span class="emotion-badge ' + emotion + '">' + emotion + '</span>' +
                            '<span class="episode-date">' + dateStr + '</span>' +
                        '</div>' +
                        '<div class="importance-bar"><div class="importance-bar-fill" style="width:' + intensityPct + '%"></div></div>' +
                        (snap.notes ? '<div class="episode-summary">' + snap.notes + '</div>' : '');
                    listEl.appendChild(card);
                });
            })
            .catch(() => { listEl.innerHTML = '<div class="empty-state">Unavailable</div>'; });
    }

    function loadTimelineSearch(query) {
        const listEl = document.getElementById('timelineEpisodesList');
        if (!listEl) return;
        const t = translations[currentLang] || translations.en;
        listEl.innerHTML = '<div class="empty-state">' + (t['timeline_loading'] || 'Loading...') + '</div>';

        fetch('/api/episodes/search?q=' + encodeURIComponent(query))
            .then(r => r.json())
            .then(data => {
                if (!data.success) { listEl.innerHTML = '<div class="empty-state">Search unavailable</div>'; return; }
                if (!data.episodes || data.episodes.length === 0) {
                    listEl.innerHTML = '<div class="empty-state">' + (t['timeline_no_episodes'] || 'No results') + '</div>';
                    return;
                }
                listEl.innerHTML = '';
                data.episodes.forEach(ep => listEl.appendChild(renderEpisodeCard(ep)));
            })
            .catch(() => { listEl.innerHTML = '<div class="empty-state">Search unavailable</div>'; });
    }

    // ===== SYSTEM HEALTH PAGE =====
    let healthRefreshInterval = null;

    function initHealthPage() {
        loadSystemHealth();
        const toggle = document.getElementById('healthAutoRefreshToggle');
        if (toggle) {
            toggle.addEventListener('change', () => {
                if (toggle.checked) {
                    healthRefreshInterval = setInterval(loadSystemHealth, 10000);
                } else {
                    if (healthRefreshInterval) {
                        clearInterval(healthRefreshInterval);
                        healthRefreshInterval = null;
                    }
                }
            });
        }
    }

    function loadSystemHealth() {
        const t = translations[currentLang] || translations.en;
        const statusCircle = document.getElementById('healthStatusCircle');
        const statusValue = document.getElementById('healthStatusValue');
        const subsystemGrid = document.getElementById('subsystemCardsGrid');
        const degradedList = document.getElementById('degradedWarningsList');

        if (!statusCircle || !statusValue) return;

        statusCircle.className = 'health-status-circle status-unknown';
        statusValue.textContent = t['health_loading'] || 'Loading...';

        fetch('/api/system/health/full')
            .then(r => r.json())
            .then(data => {
                if (!data.success) {
                    statusValue.textContent = t['health_error'] || 'Unable to load';
                    return;
                }

                // Overall status
                const status = data.status || 'unknown';
                statusCircle.className = 'health-status-circle status-' + status;
                statusValue.textContent = (t['health_' + status] || status);

                // Subsystem cards
                if (subsystemGrid && data.subsystems) {
                    subsystemGrid.innerHTML = '';
                    data.subsystems.forEach(sub => {
                        subsystemGrid.appendChild(renderSubsystemCard(sub, t));
                    });
                }

                // Degraded features
                if (degradedList && data.degraded_features) {
                    if (data.degraded_features.length === 0) {
                        degradedList.innerHTML = '<div class="empty-state">' + (t['health_no_degraded'] || 'All systems operational') + '</div>';
                    } else {
                        degradedList.innerHTML = '';
                        data.degraded_features.forEach(feat => {
                            const div = document.createElement('div');
                            div.className = 'degraded-warning';
                            div.innerHTML = '<div class="degraded-warning-advice">' + feat + '</div>';
                            degradedList.appendChild(div);
                        });
                    }
                }

                // Recommendations
                if (data.recommendations && data.recommendations.length > 0) {
                    data.recommendations.forEach(rec => {
                        const div = document.createElement('div');
                        div.className = 'degraded-warning-fix';
                        div.textContent = rec;
                        degradedList.appendChild(div);
                    });
                }

                // Load resources
                loadHealthResources(t);
            })
            .catch(() => {
                statusValue.textContent = t['health_error'] || 'Unable to load';
            });
    }

    function renderSubsystemCard(sub, t) {
        const card = document.createElement('div');
        card.className = 'subsystem-card status-' + (sub.status || 'unknown');

        const header = document.createElement('div');
        header.className = 'subsystem-card-header';

        const name = document.createElement('div');
        name.className = 'subsystem-card-name';
        name.textContent = sub.name || 'Unknown';

        const badge = document.createElement('span');
        badge.className = 'status-badge status-' + (sub.status || 'unknown');
        badge.textContent = t['health_' + (sub.status || 'unknown')] || sub.status;

        header.appendChild(name);
        header.appendChild(badge);
        card.appendChild(header);

        if (sub.latency_ms && sub.latency_ms > 0) {
            const latency = document.createElement('div');
            latency.className = 'subsystem-card-latency';
            latency.textContent = Math.round(sub.latency_ms) + 'ms';
            card.appendChild(latency);
        }

        if (sub.message) {
            const msg = document.createElement('div');
            msg.className = 'subsystem-card-message';
            msg.textContent = sub.message;
            card.appendChild(msg);
        }

        if (sub.fix) {
            const fix = document.createElement('div');
            fix.className = 'subsystem-card-fix';
            fix.textContent = (t['health_fix_suggestion'] || 'Fix: ') + sub.fix;
            card.appendChild(fix);
        }

        return card;
    }

    function loadHealthResources(t) {
        fetch('/api/system/health/resources')
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;

                const cpuBar = document.getElementById('resourceBarCpu');
                const cpuVal = document.getElementById('resourceValCpu');
                const ramBar = document.getElementById('resourceBarRam');
                const ramVal = document.getElementById('resourceValRam');
                const diskBar = document.getElementById('resourceBarDisk');
                const diskVal = document.getElementById('resourceValDisk');

                if (cpuBar && cpuVal && data.cpu_percent !== undefined) {
                    cpuBar.style.width = data.cpu_percent + '%';
                    cpuVal.textContent = data.cpu_percent.toFixed(1) + '%';
                }

                if (ramBar && ramVal && data.ram_percent !== undefined) {
                    ramBar.style.width = data.ram_percent + '%';
                    ramVal.textContent = data.ram_percent.toFixed(1) + '%';
                }

                if (diskBar && diskVal && data.disk_percent !== undefined) {
                    diskBar.style.width = data.disk_percent + '%';
                    diskVal.textContent = data.disk_percent.toFixed(1) + '%';
                }
            })
            .catch(() => {});
    }

    // ===== COGNITIVE WORKSPACE PAGE =====

    function initWorkspace() {
        loadWorkspaceSummary();
        loadWorkspaceProjects();
        loadWorkspaceTasks();
        loadWorkspaceMilestones();
        loadWorkspaceBlocked();
        setupWorkspaceForms();
    }

    function loadWorkspaceSummary() {
        const t = translations[currentLang] || translations.en;
        fetch('/api/workspace')
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                // Stats
                const el = (id) => document.getElementById(id);
                if (el('wsCompletedToday')) el('wsCompletedToday').textContent = data.completed_today || 0;
                if (el('wsProgressPct')) el('wsProgressPct').textContent = Math.round(data.progress_pct || 0) + '%';
                if (el('wsBlocked')) el('wsBlocked').textContent = data.total_blocked_tasks || 0;

                // Active project card
                const projBody = el('workspaceProjectBody');
                if (projBody && data.active_project) {
                    const ap = data.active_project;
                    projBody.innerHTML = '';
                    const name = document.createElement('div');
                    name.className = 'project-name';
                    name.textContent = ap.name || '--';
                    projBody.appendChild(name);

                    const bar = document.createElement('div');
                    bar.className = 'project-progress-bar';
                    const fill = document.createElement('div');
                    fill.className = 'project-progress-fill';
                    fill.style.width = (ap.progress_pct || 0) + '%';
                    bar.appendChild(fill);
                    projBody.appendChild(bar);

                    const pct = document.createElement('div');
                    pct.style.cssText = 'font-size:var(--font-xs);color:var(--text-secondary);margin-bottom:6px;';
                    pct.textContent = Math.round(ap.progress_pct || 0) + '% — ' + (ap.completed_tasks || 0) + '/' + (ap.total_tasks || 0);
                    projBody.appendChild(pct);

                    if (ap.health) {
                        const badge = document.createElement('span');
                        badge.className = 'project-health-badge health-' + ap.health;
                        badge.textContent = ap.health.replace('_', ' ').toUpperCase();
                        projBody.appendChild(badge);
                    }

                    // Dashboard widget
                    const dashProj = el('wsDashProject');
                    const dashFill = el('wsDashFill');
                    const dashPct = el('wsDashPct');
                    if (dashProj) dashProj.textContent = ap.name;
                    if (dashFill) dashFill.style.width = (ap.progress_pct || 0) + '%';
                    if (dashPct) dashPct.textContent = Math.round(ap.progress_pct || 0) + '%';

                    // Health stat
                    const wsHealth = el('wsHealth');
                    if (wsHealth) wsHealth.textContent = ap.health ? ap.health.replace('_', ' ').toUpperCase() : '--';
                }

                // Next task
                const nextBody = el('workspaceNextBody');
                if (nextBody && data.next_task) {
                    const nt = data.next_task;
                    nextBody.innerHTML = '';
                    const title = document.createElement('div');
                    title.className = 'next-task-title';
                    title.textContent = nt.title || '--';
                    nextBody.appendChild(title);
                    const prio = document.createElement('div');
                    prio.className = 'next-task-priority';
                    prio.textContent = (t['priority_' + (nt.priority || 'medium')] || nt.priority || '').toUpperCase();
                    nextBody.appendChild(prio);
                    const btn = document.createElement('button');
                    btn.className = 'ws-quick-resume-btn';
                    btn.textContent = t['workspace_quick_resume'] || 'Quick Resume';
                    btn.onclick = () => updateTaskStatus(nt.task_id, 'start');
                    nextBody.appendChild(btn);

                    // Dashboard widget next
                    const dashNext = el('wsDashNext');
                    if (dashNext) dashNext.textContent = nt.title || '--';
                }
            })
            .catch(() => {});
    }

    function loadWorkspaceProjects() {
        fetch('/api/workspace/projects')
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                // Populate project selector for task creation
                const sel = document.getElementById('wsTaskProject');
                if (sel) {
                    sel.innerHTML = '';
                    data.projects.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p.project_id;
                        opt.textContent = p.name;
                        sel.appendChild(opt);
                    });
                }
            })
            .catch(() => {});
    }

    function loadWorkspaceTasks() {
        const projectId = null; // all tasks
        let url = '/api/workspace/tasks';
        if (projectId) url += '?project_id=' + projectId;
        fetch(url)
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                const cols = { pending: 'wsTasksPending', in_progress: 'wsTasksInProgress', blocked: 'wsTasksBlocked', completed: 'wsTasksCompleted' };
                Object.values(cols).forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = ''; });
                data.tasks.forEach(task => {
                    const colId = cols[task.status];
                    if (!colId) return;
                    const col = document.getElementById(colId);
                    if (!col) return;
                    col.appendChild(renderTaskCard(task));
                });
            })
            .catch(() => {});
    }

    function renderTaskCard(task) {
        const card = document.createElement('div');
        card.className = 'task-card';
        const title = document.createElement('div');
        title.className = 'task-card-title';
        title.textContent = task.title;
        card.appendChild(title);

        const meta = document.createElement('div');
        meta.className = 'task-card-meta';
        const prio = document.createElement('span');
        prio.className = 'task-card-priority prio-' + (task.priority || 'medium');
        prio.textContent = (task.priority || 'medium').toUpperCase();
        meta.appendChild(prio);
        card.appendChild(meta);

        if (task.status !== 'completed' && task.status !== 'cancelled') {
            const actions = document.createElement('div');
            actions.className = 'task-card-actions';
            if (task.status === 'pending') {
                const startBtn = document.createElement('button');
                startBtn.className = 'task-card-action-btn';
                startBtn.textContent = 'Start';
                startBtn.onclick = (e) => { e.stopPropagation(); updateTaskStatus(task.task_id, 'start'); };
                actions.appendChild(startBtn);
            }
            if (task.status !== 'completed') {
                const doneBtn = document.createElement('button');
                doneBtn.className = 'task-card-action-btn';
                doneBtn.textContent = 'Done';
                doneBtn.onclick = (e) => { e.stopPropagation(); updateTaskStatus(task.task_id, 'complete'); };
                actions.appendChild(doneBtn);
            }
            card.appendChild(actions);
        }
        return card;
    }

    function loadWorkspaceMilestones() {
        fetch('/api/workspace/milestones')
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                const list = document.getElementById('workspaceMilestonesList');
                if (!list) return;
                list.innerHTML = '';
                if (data.milestones.length === 0) {
                    list.innerHTML = '<div class="empty-state">No milestones yet</div>';
                    return;
                }
                data.milestones.forEach(ms => {
                    const item = document.createElement('div');
                    item.className = 'milestone-item';
                    const name = document.createElement('div');
                    name.className = 'milestone-name';
                    name.textContent = ms.name;
                    item.appendChild(name);
                    const bar = document.createElement('div');
                    bar.className = 'milestone-progress-bar';
                    const fill = document.createElement('div');
                    fill.className = 'milestone-progress-fill';
                    fill.style.width = (ms.progress_pct || 0) + '%';
                    bar.appendChild(fill);
                    item.appendChild(bar);
                    const status = document.createElement('div');
                    status.className = 'milestone-status';
                    status.textContent = ms.status.toUpperCase() + ' — ' + (ms.task_ids ? ms.task_ids.length : 0) + ' tasks';
                    item.appendChild(status);
                    list.appendChild(item);
                });
            })
            .catch(() => {});
    }

    function loadWorkspaceBlocked() {
        fetch('/api/workspace/blocked')
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                const panel = document.getElementById('workspaceBlockedPanel');
                const list = document.getElementById('workspaceBlockedList');
                if (!panel || !list) return;
                if (data.tasks.length === 0) {
                    panel.style.display = 'none';
                    return;
                }
                panel.style.display = '';
                list.innerHTML = '';
                data.tasks.forEach(task => {
                    const div = document.createElement('div');
                    div.className = 'blocked-task-item';
                    div.textContent = task.title;
                    list.appendChild(div);
                });
            })
            .catch(() => {});
    }

    function updateTaskStatus(taskId, action) {
        fetch('/api/workspace/task/' + taskId, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        })
        .then(r => r.json())
        .then(() => {
            loadWorkspaceTasks();
            loadWorkspaceSummary();
        })
        .catch(() => {});
    }

    function setupWorkspaceForms() {
        const toggle = document.getElementById('wsFormToggle');
        const body = document.getElementById('wsFormsBody');
        if (toggle && body) {
            toggle.addEventListener('click', () => {
                body.style.display = body.style.display === 'none' ? '' : 'none';
            });
        }

        const createProjBtn = document.getElementById('wsCreateProjectBtn');
        if (createProjBtn) {
            createProjBtn.addEventListener('click', () => {
                const name = (document.getElementById('wsProjectName') || {}).value || '';
                const desc = (document.getElementById('wsProjectDesc') || {}).value || '';
                const prio = (document.getElementById('wsProjectPriority') || {}).value || 'medium';
                if (!name.trim()) return;
                fetch('/api/workspace/project', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name.trim(), description: desc, priority: prio })
                })
                .then(r => r.json())
                .then(() => {
                    document.getElementById('wsProjectName').value = '';
                    document.getElementById('wsProjectDesc').value = '';
                    loadWorkspaceProjects();
                    loadWorkspaceSummary();
                })
                .catch(() => {});
            });
        }

        const createTaskBtn = document.getElementById('wsCreateTaskBtn');
        if (createTaskBtn) {
            createTaskBtn.addEventListener('click', () => {
                const projectId = (document.getElementById('wsTaskProject') || {}).value || '';
                const title = (document.getElementById('wsTaskTitle') || {}).value || '';
                const desc = (document.getElementById('wsTaskDesc') || {}).value || '';
                const prio = (document.getElementById('wsTaskPriority') || {}).value || 'medium';
                if (!projectId || !title.trim()) return;
                fetch('/api/workspace/task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project_id: projectId, title: title.trim(), description: desc, priority: prio })
                })
                .then(r => r.json())
                .then(() => {
                    document.getElementById('wsTaskTitle').value = '';
                    document.getElementById('wsTaskDesc').value = '';
                    loadWorkspaceTasks();
                    loadWorkspaceSummary();
                })
                .catch(() => {});
            });
        }

        // Search handler
        const searchInput = document.getElementById('workspaceSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(() => {
                const q = searchInput.value.trim();
                if (!q) { loadWorkspaceTasks(); return; }
                fetch('/api/workspace/search?q=' + encodeURIComponent(q))
                    .then(r => r.json())
                    .then(data => {
                        if (!data.success) return;
                        const cols = { pending: 'wsTasksPending', in_progress: 'wsTasksInProgress', blocked: 'wsTasksBlocked', completed: 'wsTasksCompleted' };
                        Object.values(cols).forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = ''; });
                        (data.tasks || []).forEach(task => {
                            const colId = cols[task.status];
                            if (!colId) return;
                            const col = document.getElementById(colId);
                            if (!col) return;
                            col.appendChild(renderTaskCard(task));
                        });
                    })
                    .catch(() => {});
            }, 300));
        }
    }

    // Load workspace dashboard widget on page load
    function loadWorkspaceDashWidget() {
        fetch('/api/workspace')
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                const el = (id) => document.getElementById(id);
                if (data.active_project) {
                    const dashProj = el('wsDashProject');
                    const dashFill = el('wsDashFill');
                    const dashPct = el('wsDashPct');
                    if (dashProj) dashProj.textContent = data.active_project.name || '--';
                    if (dashFill) dashFill.style.width = (data.active_project.progress_pct || 0) + '%';
                    if (dashPct) dashPct.textContent = Math.round(data.active_project.progress_pct || 0) + '%';
                }
                if (data.next_task) {
                    const dashNext = el('wsDashNext');
                    if (dashNext) dashNext.textContent = data.next_task.title || '--';
                }
            })
            .catch(() => {});
    }
    // Load dashboard widget once on init
    setTimeout(loadWorkspaceDashWidget, 1500);
});
