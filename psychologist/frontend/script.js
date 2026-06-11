// Cognitive Self-Evolving Mind Dashboard - Enhanced Version
document.addEventListener('DOMContentLoaded', () => {
    let step = 0;
    let currentFilter = 'all';
    let selectedInputType = 'Observation';
    let inputHistory = JSON.parse(localStorage.getItem('cognitiveMindHistory') || '[]');
    let currentLanguage = localStorage.getItem('cognitiveMindLanguage') || 'en';
    
    // i18n System - Embedded translations
    const translations = {
        en: {
            "system_name": "Cognitive Mind v2.0",
            "status_online": "ONLINE & EVOLVING",
            "nav_dashboard": "Main Dashboard",
            "nav_emotions": "Emotion Panel",
            "nav_needs": "Internal Needs",
            "nav_beliefs": "Belief System",
            "nav_goals": "Goal Generation",
            "nav_conflicts": "Cognitive Conflicts",
            "nav_identity": "Self-Identity",
            "nav_memory": "Memory Timeline",
            "nav_graph": "Knowledge Graph",
            "nav_debate": "Internal Debate",
            "nav_simulation": "Simulation Panel",
            "nav_history": "Input History",
            "title_dashboard": "Cognitive State Overview",
            "title_emotions": "Emotion State",
            "title_needs": "Internal Needs",
            "title_beliefs": "Belief System",
            "title_goals": "Autonomous Goals",
            "title_conflicts": "Cognitive Conflicts",
            "title_identity": "Self-Identity Model",
            "title_memory": "Memory Timeline",
            "title_graph": "Knowledge Graph",
            "title_debate": "Internal Debate",
            "title_simulation": "Future Simulation",
            "title_history": "Input History",
            "card_header_cognitive_state": "CURRENT COGNITIVE STATE",
            "card_header_active_emotional": "ACTIVE EMOTIONAL STATE",
            "card_header_dominant_goal": "CURRENT DOMINANT GOAL",
            "card_header_system_metrics": "SYSTEM METRICS",
            "sub_exploring": "Adapting to new data",
            "sub_priority_high": "Priority: HIGH",
            "metric_confidence": "CONFIDENCE LEVEL",
            "metric_stability": "INTERNAL STABILITY",
            "metric_energy": "COGNITIVE ENERGY",
            "filter_all": "All Beliefs",
            "filter_strong": "Strong Beliefs",
            "filter_weak": "Weak Beliefs",
            "filter_conflicted": "Conflicted",
            "filter_new": "New Beliefs",
            "badge_new": "NEW",
            "badge_conflicted": "CONFLICTED",
            "priority_high": "HIGH",
            "priority_medium": "MEDIUM",
            "priority_low": "LOW",
            "status_active": "Active",
            "status_paused": "Paused",
            "status_completed": "Completed",
            "status_abandoned": "Abandoned",
            "source_need_exploration": "Exploration",
            "source_need_social": "Social",
            "source_need_knowledge": "Knowledge",
            "source_need_achievement": "Achievement",
            "emotion_influence_curiosity": "Curiosity",
            "emotion_influence_trust": "Trust",
            "emotion_influence_confidence": "Confidence",
            "emotion_influence_pride": "Pride",
            "emotion_influence_fear": "Fear",
            "identity_self_confidence": "SELF-CONFIDENCE",
            "identity_self_consistency": "SELF-CONSISTENCY",
            "identity_knowledge_gaps": "KNOWLEDGE GAPS",
            "identity_decision_quality": "DECISION QUALITY",
            "identity_emotional_balance": "EMOTIONAL BALANCE",
            "identity_value_stability": "VALUE STABILITY",
            "sim_scenario_header": "Possible Future Outcome",
            "sim_scenario_text": "Explore new social interaction will build trust",
            "sim_risk_score": "Risk Score",
            "sim_reward_score": "Reward Score",
            "sim_consequence_header": "Emotional Consequence",
            "sim_consequence_text": "Increased trust and curiosity; mild excitement",
            "sim_action_header": "Recommended Action",
            "sim_action_text": "Engage in the social interaction",
            "history_search_placeholder": "Search inputs...",
            "history_filter_all": "All Types",
            "history_filter_observation": "Observation",
            "history_filter_emotion": "Emotion",
            "history_filter_memory": "Memory",
            "history_filter_belief": "Belief",
            "history_filter_goal": "Goal",
            "history_filter_question": "Question",
            "history_filter_experience": "Experience",
            "history_filter_relationship": "Relationship Event",
            "history_filter_environmental": "Environmental Event",
            "history_meta_impact": "Impact",
            "console_thought_stream": "Real-Time Thought Stream",
            "console_input_interface": "Cognitive Input Interface",
            "console_classification_label": "Select Input Type:",
            "console_input_placeholder": "Enter observation, event, emotion, memory, belief, question, or experience...",
            "console_emotion_injection": "Emotion Injection Controls",
            "console_submit_button": "Inject Into Mind",
            "console_response_title": "Cognitive Response Analysis",
            "console_response_concepts": "Detected Concepts",
            "console_response_beliefs": "Affected Beliefs",
            "console_response_emotions": "Updated Emotions",
            "console_response_memory": "Memory Impact",
            "console_response_prediction": "Predicted Outcome",
            "flow_step_1": "Input Received",
            "flow_step_2": "Context Analysis",
            "flow_step_3": "Belief Evaluation",
            "flow_step_4": "Memory Storage",
            "flow_step_5": "Emotion Update",
            "flow_step_6": "Goal Assessment",
            "flow_step_7": "Identity Impact",
            "type_observation": "Observation",
            "type_emotion": "Emotion",
            "type_memory": "Memory",
            "type_belief": "Belief",
            "type_goal": "Goal",
            "type_question": "Question",
            "type_experience": "Experience",
            "type_relationship": "Relationship Event",
            "type_environmental": "Environmental Event",
            "slider_happiness": "Happiness",
            "slider_sadness": "Sadness",
            "slider_fear": "Fear",
            "slider_anger": "Anger",
            "slider_curiosity": "Curiosity",
            "slider_trust": "Trust",
            "slider_motivation": "Motivation",
            "slider_stress": "Stress",
            "influence_emotions": "Emotions",
            "influence_goals": "Goals",
            "influence_identity": "Identity",
            "influence_beliefs": "Beliefs",
            "influence_memory": "Memory",
            "language_toggle_bangla": "বাংলা",
            "language_toggle_english": "English",
            "thought_current_thought": "Current Thought",
            "thought_internal_reasoning": "Internal Reasoning",
            "thought_decision_process": "Decision Process",
            "thought_active_goal": "Active Goal",
            "thought_goal_queue": "Goal Queue",
            "thought_emotional_state": "Emotional State",
            "thought_attention_focus": "Attention Focus",
            "thought_memory_recall": "Memory Recall",
            "thought_context_analysis": "Context Analysis",
            "thought_task_planning": "Task Planning",
            "thought_risk_assessment": "Risk Assessment",
            "thought_confidence_score": "Confidence Score",
            "thought_learning_progress": "Learning Progress",
            "thought_self_reflection": "Self Reflection",
            "thought_priority_level": "Priority Level",
            "thought_system_status": "System Status",
            "thought_observation": "Observation",
            "thought_prediction": "Prediction",
            "thought_action_selection": "Action Selection",
            "status_processing": "Processing",
            "status_completed_alt": "Completed",
            "status_waiting": "Waiting",
            "status_thinking": "Thinking",
            "status_analyzing": "Analyzing",
            "status_learning": "Learning",
            "status_monitoring": "Monitoring",
            "status_generating_plan": "Generating Plan",
            "status_searching_memory": "Searching Memory",
            "status_evaluating_options": "Evaluating Options",
            "status_building_response": "Building Response"
  },
        bn_bd: {
            "system_name": "কগনিটিভ মাইন্ড v2.0",
            "status_online": "অনলাইন এবং বিকশিত হচ্ছে",
            "nav_dashboard": "প্রধান ড্যাশবোর্ড",
            "nav_emotions": "আবেগ প্যানেল",
            "nav_needs": "অন্তর্নিহিত প্রয়োজনীয়তা",
            "nav_beliefs": "বিশ্বাস ব্যবস্থা",
            "nav_goals": "লক্ষ্য উৎপাদন",
            "nav_conflicts": "কগনিটিভ দ্বন্দ্ব",
            "nav_identity": "আত্ম-পরিচয়",
            "nav_memory": "স্মৃতি টাইমলাইন",
            "nav_graph": "জ্ঞান গ্রাফ",
            "nav_debate": "অন্তর্নিহিত বিতর্ক",
            "nav_simulation": "সিমুলেশন প্যানেল",
            "nav_history": "ইনপুট ইতিহাস",
            "title_dashboard": "কগনিটিভ অবস্থার ওভারভিউ",
            "title_emotions": "আবেগের অবস্থা",
            "title_needs": "অন্তর্নিহিত প্রয়োজনীয়তা",
            "title_beliefs": "বিশ্বাস ব্যবস্থা",
            "title_goals": "স্বায়ত্তশাসিত লক্ষ্য",
            "title_conflicts": "কগনিটিভ দ্বন্দ্ব",
            "title_identity": "আত্ম-পরিচয় মডেল",
            "title_memory": "স্মৃতি টাইমলাইন",
            "title_graph": "জ্ঞান গ্রাফ",
            "title_debate": "অন্তর্নিহিত বিতর্ক",
            "title_simulation": "ভবিষ্যৎ সিমুলেশন",
            "title_history": "ইনপুট ইতিহাস",
            "card_header_cognitive_state": "বর্তমান কগনিটিভ অবস্থা",
            "card_header_active_emotional": "সক্রিয় আবেগের অবস্থা",
            "card_header_dominant_goal": "বর্তমান প্রধান লক্ষ্য",
            "card_header_system_metrics": "সিস্টেম মেট্রিক্স",
            "sub_exploring": "নতুন ডেটার সাথে খাপ খাইয়ে নিচ্ছে",
            "sub_priority_high": "অগ্রাধিকার: উচ্চ",
            "metric_confidence": "আত্মবিশ্বাসের মাত্রা",
            "metric_stability": "অন্তর্নিহিত স্থিতিশীলতা",
            "metric_energy": "কগনিটিভ শক্তি",
            "filter_all": "সব বিশ্বাস",
            "filter_strong": "শক্তিশালী বিশ্বাস",
            "filter_weak": "দুর্বল বিশ্বাস",
            "filter_conflicted": "দ্বন্দ্বিত",
            "filter_new": "নতুন বিশ্বাস",
            "badge_new": "নতুন",
            "badge_conflicted": "দ্বন্দ্বিত",
            "priority_high": "উচ্চ",
            "priority_medium": "মাঝারি",
            "priority_low": "কম",
            "status_active": "সক্রিয়",
            "status_paused": "স্থগিত",
            "status_completed": "সম্পন্ন",
            "status_abandoned": "পরিত্যক্ত",
            "source_need_exploration": "অন্বেষণ",
            "source_need_social": "সামাজিক",
            "source_need_knowledge": "জ্ঞান",
            "source_need_achievement": "অর্জন",
            "emotion_influence_curiosity": "কৌতূহল",
            "emotion_influence_trust": "বিশ্বাস",
            "emotion_influence_confidence": "আত্মবিশ্বাস",
            "emotion_influence_pride": "অহংকার",
            "emotion_influence_fear": "ভয়",
            "identity_self_confidence": "আত্মবিশ্বাস",
            "identity_self_consistency": "আত্ম-সামঞ্জস্য",
            "identity_knowledge_gaps": "জ্ঞানের ফাঁক",
            "identity_decision_quality": "সিদ্ধান্তের গুণমান",
            "identity_emotional_balance": "আবেগের ভারসাম্য",
            "identity_value_stability": "মূল্যের স্থিতিশীলতা",
            "sim_scenario_header": "সম্ভাব্য ভবিষ্যৎ ফলাফল",
            "sim_scenario_text": "নতুন সামাজিক মিথস্ক্রিয়া বিশ্বাস বাড়াবে",
            "sim_risk_score": "ঝুঁকি স্কোর",
            "sim_reward_score": "পুরস্কার স্কোর",
            "sim_consequence_header": "আবেগের পরিণতি",
            "sim_consequence_text": "বৃদ্ধি পাওয়া বিশ্বাস ও কৌতূহল; হালকা উত্তেজনা",
            "sim_action_header": "সুপারিশকৃত পদক্ষেপ",
            "sim_action_text": "সামাজিক মিথস্ক্রিয়াতে অংশগ্রহণ করুন",
            "history_search_placeholder": "ইনপুট সার্চ করুন...",
            "history_filter_all": "সব ধরন",
            "history_filter_observation": "পর্যবেক্ষণ",
            "history_filter_emotion": "আবেগ",
            "history_filter_memory": "স্মৃতি",
            "history_filter_belief": "বিশ্বাস",
            "history_filter_goal": "লক্ষ্য",
            "history_filter_question": "প্রশ্ন",
            "history_filter_experience": "অভিজ্ঞতা",
            "history_filter_relationship": "সম্পর্কের ঘটনা",
            "history_filter_environmental": "পরিবেশের ঘটনা",
            "history_meta_impact": "প্রভাব",
            "console_thought_stream": "রিয়েল-টাইম চিন্তার প্রবাহ",
            "console_input_interface": "কগনিটিভ ইনপুট ইন্টারফেস",
            "console_classification_label": "ইনপুটের ধরন নির্বাচন করুন:",
            "console_input_placeholder": "পর্যবেক্ষণ, ঘটনা, আবেগ, স্মৃতি, বিশ্বাস, প্রশ্ন বা অভিজ্ঞতা লিখুন...",
            "console_emotion_injection": "আবেগ ইনজেকশন কন্ট্রোল",
            "console_submit_button": "মস্তিষ্কে ইনজেক্ট করুন",
            "console_response_title": "কগনিটিভ প্রতিক্রিয়া বিশ্লেষণ",
            "console_response_concepts": "সনাক্তকৃত ধারণা",
            "console_response_beliefs": "প্রভাবিত বিশ্বাস",
            "console_response_emotions": "আপডেট করা আবেগ",
            "console_response_memory": "স্মৃতির প্রভাব",
            "console_response_prediction": "পূর্বাভাসিত ফলাফল",
            "flow_step_1": "ইনপুট প্রাপ্ত হয়েছে",
            "flow_step_2": "কনটেক্সট বিশ্লেষণ",
            "flow_step_3": "বিশ্বাস মূল্যায়ন",
            "flow_step_4": "স্মৃতি সংরক্ষণ",
            "flow_step_5": "আবেগ আপডেট",
            "flow_step_6": "লক্ষ্য মূল্যায়ন",
            "flow_step_7": "পরিচয়ের প্রভাব",
            "type_observation": "পর্যবেক্ষণ",
            "type_emotion": "আবেগ",
            "type_memory": "স্মৃতি",
            "type_belief": "বিশ্বাস",
            "type_goal": "লক্ষ্য",
            "type_question": "প্রশ্ন",
            "type_experience": "অভিজ্ঞতা",
            "type_relationship": "সম্পর্কের ঘটনা",
            "type_environmental": "পরিবেশের ঘটনা",
            "slider_happiness": "সুখ",
            "slider_sadness": "দুঃখ",
            "slider_fear": "ভয়",
            "slider_anger": "রাগ",
            "slider_curiosity": "কৌতূহল",
            "slider_trust": "বিশ্বাস",
            "slider_motivation": "উদ্দীপনা",
            "slider_stress": "চাপ",
            "influence_emotions": "আবেগ",
            "influence_goals": "লক্ষ্য",
            "influence_identity": "পরিচয়",
            "influence_beliefs": "বিশ্বাস",
            "influence_memory": "স্মৃতি",
            "language_toggle_bangla": "বাংলা",
            "language_toggle_english": "English",
            "thought_current_thought": "বর্তমান চিন্তা",
            "thought_internal_reasoning": "অভ্যন্তরীণ বিশ্লেষণ",
            "thought_decision_process": "সিদ্ধান্ত গ্রহণ প্রক্রিয়া",
            "thought_active_goal": "সক্রিয় লক্ষ্য",
            "thought_goal_queue": "লক্ষ্য তালিকা",
            "thought_emotional_state": "আবেগীয় অবস্থা",
            "thought_attention_focus": "মনোযোগের কেন্দ্র",
            "thought_memory_recall": "স্মৃতি পুনরুদ্ধার",
            "thought_context_analysis": "প্রেক্ষাপট বিশ্লেষণ",
            "thought_task_planning": "কাজের পরিকল্পনা",
            "thought_risk_assessment": "ঝুঁকি মূল্যায়ন",
            "thought_confidence_score": "আত্মবিশ্বাসের মাত্রা",
            "thought_learning_progress": "শেখার অগ্রগতি",
            "thought_self_reflection": "আত্ম-পর্যালোচনা",
            "thought_priority_level": "অগ্রাধিকারের স্তর",
            "thought_system_status": "সিস্টেমের অবস্থা",
            "thought_observation": "পর্যবেক্ষণ",
            "thought_prediction": "পূর্বাভাস",
            "thought_action_selection": "কর্ম নির্বাচন",
            "status_processing": "প্রক্রিয়াকরণ চলছে",
            "status_completed_alt": "সম্পন্ন হয়েছে",
            "status_waiting": "অপেক্ষমাণ",
            "status_thinking": "চিন্তা করছে",
            "status_analyzing": "বিশ্লেষণ করছে",
            "status_learning": "শিখছে",
            "status_monitoring": "পর্যবেক্ষণ করছে",
            "status_generating_plan": "পরিকল্পনা তৈরি করছে",
            "status_searching_memory": "স্মৃতিতে অনুসন্ধান করছে",
            "status_evaluating_options": "বিকল্পগুলো মূল্যায়ন করছে",
            "status_building_response": "উত্তর প্রস্তুত করছে"
  }
    };
    
    function applyTranslations(lang) {
        const t = translations[lang] || translations.en;
        
        // Update text content
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (t[key]) {
                el.textContent = t[key];
            }
        });
        
        // Update placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (t[key]) {
                el.placeholder = t[key];
            }
        });
        
        // Update html lang attribute
        document.documentElement.lang = lang === 'bn_bd' ? 'bn' : 'en';
        
        // Update language toggle button
        const langToggle = document.getElementById('languageToggle');
        if (langToggle) {
            langToggle.textContent = lang === 'en' ? t.language_toggle_bangla : t.language_toggle_english;
            langToggle.setAttribute('data-i18n', lang === 'en' ? 'language_toggle_bangla' : 'language_toggle_english');
        }
        
        // Save language preference
        localStorage.setItem('cognitiveMindLanguage', lang);
        currentLanguage = lang;
    }
    
    // Apply initial language
    applyTranslations(currentLanguage);

    // Initial Data
    let initialEmotions = {
        curiosity: 78,
        fear: 23,
        confidence: 85,
        doubt: 15,
        motivation: 70,
        stress: 35,
        trust: 60,
        frustration: 18
    };

    let initialNeeds = {
        knowledge: 45,
        security: 92,
        exploration: 85,
        social: 65,
        achievement: 55,
        stabilityNeed: 75,
        autonomy: 88
    };

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

    const identityMetrics = {
        confidence: 85,
        consistency: 78,
        knowledgeGaps: 23,
        decisionQuality: 81,
        emotionalBalance: 69,
        valueStability: 74
    };

    let memoryEvents = [
        { type: "Emotional Shift", content: "Curiosity rose to 78%", time: "0:02" },
        { type: "Goal Updated", content: "Added goal: Explore territories", time: "0:45" },
        { type: "Belief Change", content: "Confidence in social trust increased", time: "1:12" },
        { type: "Important Event", content: "New interaction detected", time: "1:58" },
        { type: "Identity Change", content: "Self-consistency score updated", time: "2:30" },
        { type: "Emotional Shift", content: "Stress reduced to 35%", time: "2:45" }
    ];

    let thoughtStreamData = [];
    let influenceValues = {
        emotions: 65,
        goals: 45,
        identity: 35,
        beliefs: 50,
        memory: 40
    };

    // DOM Elements
    const navButtons = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.section');
    const cognitiveInput = document.getElementById('cognitiveInput');
    const submitBtn = document.getElementById('submitBtn');
    const processingFlow = document.getElementById('processingFlow');
    const responsePanel = document.getElementById('responsePanel');
    const micBtn = document.getElementById('micBtn');
    const historyList = document.getElementById('historyList');
    const historySearch = document.getElementById('historySearch');
    const historyFilter = document.getElementById('historyFilter');
    const pillButtons = document.querySelectorAll('.pill-btn');
    const emotionSliders = document.querySelectorAll('.emotion-slider');
    const languageToggle = document.getElementById('languageToggle');

    // Language toggle event
    languageToggle.addEventListener('click', () => {
        const newLang = currentLanguage === 'en' ? 'bn_bd' : 'en';
        applyTranslations(newLang);
    });

    // Initialize Everything
    renderBeliefs();
    renderGoals();
    renderConflicts();
    renderMemoryTimeline();
    renderHistory();
    drawKnowledgeGraph();
    drawRadialCharts();
    updateEmotionBars(initialEmotions);
    updateNeeds(initialNeeds);
    updateDashboard({
        step,
        confidence: identityMetrics.confidence,
        stability: identityMetrics.consistency,
        energy: identityMetrics.emotionalBalance
    });
    startThoughtStream();
    updateClock();
    setInterval(updateClock, 1000);
    setInterval(() => {
        simulateCognitiveEvent();
    }, 5000);

    // --- Helper Functions ---
    function updateClock() {
        const now = new Date();
        const clock = document.querySelector('.clock');
        if (clock) clock.textContent = now.toLocaleTimeString('en-US', { hour12: false });
    }

    function animateNumber(element, start, end, duration = 1000) {
        let startTime = null;
        const animate = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const current = Math.floor(start + (end - start) * progress);
            element.textContent = current;
            if (progress < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    }

    // --- Rendering Functions ---
    function renderBeliefs() {
        const beliefListEl = document.getElementById('beliefList');
        let filtered = beliefs;
        
        if (currentFilter === 'strong') filtered = beliefs.filter(b => b.confidence >= 0.8);
        else if (currentFilter === 'weak') filtered = beliefs.filter(b => b.confidence < 0.7);
        else if (currentFilter === 'conflicted') filtered = beliefs.filter(b => b.contradictions > 0);
        else if (currentFilter === 'new') filtered = beliefs.filter(b => b.isNew);

        beliefListEl.innerHTML = filtered.map(belief => `
            <div class="belief-item">
                <div class="belief-top">
                    <div class="belief-name">${belief.name}</div>
                    <div class="belief-confidence">${Math.round(belief.confidence * 100)}%</div>
                </div>
                <div class="belief-meta">
                    <div>Evidence: ${belief.evidence}</div>
                    <div>Contradictions: ${belief.contradictions}</div>
                    <div>Updated: ${belief.lastUpdated}</div>
                    ${belief.isNew ? '<span class="badge badge-new">NEW</span>' : ''}
                    ${belief.contradictions > 0 ? '<span class="badge badge-conflicted">CONFLICTED</span>' : ''}
                </div>
            </div>
        `).join('');
    }

    function renderGoals() {
        const goalsGridEl = document.getElementById('goalsGrid');
        goalsGridEl.innerHTML = goals.map(goal => `
            <div class="goal-card ${goal.status.toLowerCase()}">
                <div class="goal-title">${goal.title}</div>
                <div class="goal-meta">
                    <span>Priority: ${goal.priority}</span>
                    <span>Source: ${goal.sourceNeed}</span>
                    <span>Emotion: ${goal.emotionalInfluence}</span>
                    <span class="status-tag status-${goal.status.toLowerCase()}">${goal.status}</span>
                </div>
            </div>
        `).join('');
    }

    function renderConflicts() {
        const conflictGridEl = document.getElementById('conflictGrid');
        conflictGridEl.innerHTML = conflicts.map(conflict => `
            <div class="conflict-item">
                <div class="conflict-title">${conflict.left} vs ${conflict.right}</div>
                <div class="conflict-bar">
                    <div class="conflict-left" style="width: ${conflict.leftPercent}%">${conflict.left} ${conflict.leftPercent}%</div>
                    <div class="conflict-right" style="width: ${conflict.rightPercent}%">${conflict.right} ${conflict.rightPercent}%</div>
                </div>
            </div>
        `).join('');
    }

    function renderMemoryTimeline() {
        const memoryTimelineEl = document.getElementById('memoryTimeline');
        memoryTimelineEl.innerHTML = memoryEvents.map(event => `
            <div class="memory-item">
                <div class="memory-time">${event.time}</div>
                <div class="memory-type">${event.type}</div>
                <div class="memory-content">${event.content}</div>
            </div>
        `).join('');
    }

    function renderHistory() {
        const historyListEl = document.getElementById('historyList');
        let filtered = inputHistory;
        
        const searchTerm = historySearch.value.toLowerCase();
        if (searchTerm) {
            filtered = inputHistory.filter(item => 
                item.text.toLowerCase().includes(searchTerm)
            );
        }
        
        const filterType = historyFilter.value;
        if (filterType !== 'all') {
            filtered = filtered.filter(item => item.type === filterType);
        }
        
        historyListEl.innerHTML = filtered.map(item => `
            <div class="history-item">
                <div class="history-content">
                    <div class="history-text">${item.text}</div>
                    <div class="history-meta">
                        <span class="history-type">${item.type}</span>
                        <span>Impact: ${item.impact}%</span>
                        <span>${item.time}</span>
                    </div>
                </div>
                <button class="history-delete" onclick="deleteHistoryItem('${item.id}')">×</button>
            </div>
        `).join('');
    }

    function updateEmotionBars(emotions) {
        Object.entries(emotions).forEach(([key, value]) => {
            const fillId = `${key}Fill`;
            const percentId = `${key}Percent`;
            const fillEl = document.getElementById(fillId);
            const percentEl = document.getElementById(percentId);
            if (fillEl && percentEl) {
                fillEl.style.width = `${value}%`;
                animateNumber(percentEl, parseInt(percentEl.textContent), value);
            }
        });
        
        // Update dominant emotion display
        let dominant = Object.entries(emotions).reduce((a, b) => a[1] > b[1] ? a : b);
        document.getElementById('dominantEmotion').textContent = dominant[0].charAt(0).toUpperCase() + dominant[0].slice(1);
        document.querySelector('.dominant-intensity').textContent = `${dominant[1]}%`;
    }

    function updateNeeds(needs) {
        Object.entries(needs).forEach(([key, value]) => {
            const fillId = `${key}Fill`;
            const percentId = `${key}Percent`;
            const fillEl = document.getElementById(fillId);
            const percentEl = document.getElementById(percentId);
            if (fillEl && percentEl) {
                fillEl.style.width = `${value}%`;
                animateNumber(percentEl, parseInt(percentEl.textContent), value);
            }
        });
    }

    function updateDashboard(state) {
        step = state.step;
        animateNumber(document.getElementById('stepCounter'), step, state.step);
        animateNumber(document.getElementById('confidenceLevel'), parseInt(document.getElementById('confidenceLevel').textContent), state.confidence);
        animateNumber(document.getElementById('stabilityScore'), parseInt(document.getElementById('stabilityScore').textContent), state.stability);
        animateNumber(document.getElementById('cognitiveEnergy'), parseInt(document.getElementById('cognitiveEnergy').textContent), state.energy);
        document.getElementById('energyFill').style.width = `${state.energy}%`;
        
        // Update identity display if section is present
        const idConf = document.getElementById('identityConfidence');
        if (idConf) animateNumber(idConf, parseInt(idConf.textContent), identityMetrics.confidence);
        const idCons = document.getElementById('identityConsistency');
        if (idCons) animateNumber(idCons, parseInt(idCons.textContent), identityMetrics.consistency);
        const idGaps = document.getElementById('knowledgeGaps');
        if (idGaps) animateNumber(idGaps, parseInt(idGaps.textContent), identityMetrics.knowledgeGaps);
        const idDec = document.getElementById('decisionQuality');
        if (idDec) animateNumber(idDec, parseInt(idDec.textContent), identityMetrics.decisionQuality);
        const idEmo = document.getElementById('emotionalBalance');
        if (idEmo) animateNumber(idEmo, parseInt(idEmo.textContent), identityMetrics.emotionalBalance);
        const idVal = document.getElementById('valueStability');
        if (idVal) animateNumber(idVal, parseInt(idVal.textContent), identityMetrics.valueStability);
    }

    function drawKnowledgeGraph() {
        const canvas = document.getElementById('knowledgeGraph');
        const ctx = canvas.getContext('2d');
        
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
        
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.clearRect(0, 0, width, height);
        
        const nodes = [
            { x: width / 2, y: height / 3, label: 'SELF', radius: 45, color: '#00f0ff' },
            { x: width / 4, y: height / 2, label: 'BELIEFS', radius: 35, color: '#00ff88' },
            { x: 3 * width / 4, y: height / 2, label: 'GOALS', radius: 35, color: '#a855f7' },
            { x: width / 3, y: 2 * height / 3, label: 'VALUES', radius: 30, color: '#0066ff' },
            { x: 2 * width / 3, y: 2 * height / 3, label: 'EMOTIONS', radius: 38, color: '#ff3366' },
            { x: width / 5, y: height / 1.5, label: 'MEMORIES', radius: 32, color: '#ff9500' }
        ];
        
        const edges = [[0,1],[0,2],[0,4],[1,3],[1,5],[2,3],[2,4],[3,4],[4,5]];
        
        // Draw edges first
        edges.forEach(([a, b]) => {
            ctx.beginPath();
            ctx.strokeStyle = 'rgba(0,240,255,0.3)';
            ctx.lineWidth = 2;
            ctx.moveTo(nodes[a].x, nodes[a].y);
            ctx.lineTo(nodes[b].x, nodes[b].y);
            ctx.stroke();
        });
        
        // Draw nodes
        nodes.forEach(node => {
            // Glow effect
            ctx.shadowBlur = 25;
            ctx.shadowColor = node.color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
            ctx.fillStyle = `${node.color}20`;
            ctx.fill();
            
            // Circle border
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
            ctx.strokeStyle = node.color;
            ctx.lineWidth = 3;
            ctx.stroke();
            
            // Label
            ctx.shadowBlur = 0;
            ctx.fillStyle = '#e0e0e0';
            ctx.font = 'bold 14px Segoe UI';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(node.label, node.x, node.y);
        });
    }

    function drawRadialCharts() {
        const chartData = [
            { id: 'radialEmotions', value: influenceValues.emotions, color: '#00f0ff' },
            { id: 'radialGoals', value: influenceValues.goals, color: '#a855f7' },
            { id: 'radialIdentity', value: influenceValues.identity, color: '#00ff88' },
            { id: 'radialBeliefs', value: influenceValues.beliefs, color: '#0066ff' },
            { id: 'radialMemory', value: influenceValues.memory, color: '#ff9500' }
        ];
        
        chartData.forEach(chart => {
            const canvas = document.getElementById(chart.id);
            if (canvas) {
                const ctx = canvas.getContext('2d');
                const width = canvas.width;
                const height = canvas.height;
                const radius = 45;
                const centerX = width / 2;
                const centerY = height / 2;
                
                ctx.clearRect(0,0,width,height);
                
                // Background circle
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                ctx.strokeStyle = 'rgba(255,255,255,0.1)';
                ctx.lineWidth = 8;
                ctx.stroke();
                
                // Progress circle
                const progress = chart.value / 100;
                const startAngle = -Math.PI / 2;
                const endAngle = startAngle + 2 * Math.PI * progress;
                
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, startAngle, endAngle);
                ctx.strokeStyle = chart.color;
                ctx.lineWidth = 8;
                ctx.lineCap = 'round';
                ctx.shadowBlur = 15;
                ctx.shadowColor = chart.color;
                ctx.stroke();
                
                // Value display
                ctx.shadowBlur = 0;
                ctx.fillStyle = '#e0e0e0';
                ctx.font = 'bold 18px Segoe UI';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(`${Math.round(chart.value)}%`, centerX, centerY);
            }
        });
    }

    function startThoughtStream() {
        const thoughtStreamEl = document.getElementById('thoughtStream');
        
        const thoughtTemplates = [
            { label: 'thought_observation', content: 'Analyzing emotional significance of input...', bn: 'ইনপুটের আবেগিক তাৎপর্য বিশ্লেষণ করা হচ্ছে...' },
            { label: 'thought_memory_recall', content: 'Comparing with past experiences...', bn: 'অতীতের অভিজ্ঞতার সাথে তুলনা করা হচ্ছে...' },
            { label: 'thought_task_planning', content: 'Evaluating belief consistency...', bn: 'বিশ্বাসের সামঞ্জস্য মূল্যায়ন করা হচ্ছে...' },
            { label: 'thought_active_goal', content: 'Calculating goal priority shifts...', bn: 'লক্ষ্যের অগ্রাধিকার পরিবর্তন গণনা করা হচ্ছে...' },
            { label: 'thought_context_analysis', content: 'Processing memory consolidation...', bn: 'স্মৃতি সংযোজন প্রক্রিয়াকরণ করা হচ্ছে...' },
            { label: 'thought_prediction', content: 'Simulating future outcomes...', bn: 'ভবিষ্যৎ ফলাফলের সিমুলেশন করা হচ্ছে...' },
            { label: 'thought_self_reflection', content: 'Assessing identity impact...', bn: 'পরিচয়ের প্রভাব মূল্যায়ন করা হচ্ছে...' },
            { label: 'thought_confidence_score', content: 'Reflecting on decision quality...', bn: 'সিদ্ধান্তের গুণমানের প্রতি প্রতিচ্ছবি করা হচ্ছে...' },
            { label: 'thought_system_status', content: 'Updating cognitive state models...', bn: 'জ্ঞানীয় অবস্থার মডেল আপডেট করা হচ্ছে...' },
            { label: 'thought_learning_progress', content: 'Integrating new information...', bn: 'নতুন তথ্য একীভূত করা হচ্ছে...' },
            { label: 'thought_internal_reasoning', content: 'Running internal reasoning chains...', bn: 'অভ্যন্তরীণ যুক্তি চালু করা হচ্ছে...' },
            { label: 'thought_decision_process', content: 'Evaluating possible decision paths...', bn: 'সম্ভাব্য সিদ্ধান্তের পথ মূল্যায়ন করা হচ্ছে...' },
            { label: 'thought_goal_queue', content: 'Updating the active goal queue...', bn: 'সক্রিয় লক্ষ্যের তালিকা আপডেট করা হচ্ছে...' },
            { label: 'thought_emotional_state', content: 'Monitoring current emotional state...', bn: 'বর্তমান আবেগীয় অবস্থা পর্যবেক্ষণ করা হচ্ছে...' },
            { label: 'thought_attention_focus', content: 'Redirecting attention to new stimuli...', bn: 'নতুন উদ্দীপনার দিকে মনোযোগ নিয়ে যাওয়া হচ্ছে...' },
            { label: 'thought_risk_assessment', content: 'Performing risk assessment of options...', bn: 'বিকল্পগুলোর ঝুঁকি মূল্যায়ন করা হচ্ছে...' },
            { label: 'thought_priority_level', content: 'Recomputing priority levels for tasks...', bn: 'কাজগুলোর জন্য অগ্রাধিকারের স্তর পুনরায় গণনা করা হচ্ছে...' },
            { label: 'thought_action_selection', content: 'Selecting the optimal action to take...', bn: 'গ্রহণের জন্য সর্বোত্তম কর্ম নির্বাচন করা হচ্ছে...' }
        ];

        const addThought = () => {
            const t = translations[currentLanguage] || translations.en;
            const template = thoughtTemplates[Math.floor(Math.random() * thoughtTemplates.length)];
            const label = t[template.label] || template.label;
            const content = currentLanguage === 'bn_bd' ? template.bn : template.content;
            
            const now = new Date();
            const timeStr = now.toLocaleTimeString(currentLanguage === 'bn_bd' ? 'bn-BD' : 'en-US', { hour12: false });
            
            const thought = `<div class="thought-item">
                <div class="thought-time">${timeStr}</div>
                <strong>${label}:</strong> ${content}
            </div>`;
            
            if (thoughtStreamEl) {
                thoughtStreamEl.innerHTML = thought + thoughtStreamEl.innerHTML;
                if (thoughtStreamEl.children.length > 15) {
                    thoughtStreamEl.removeChild(thoughtStreamEl.lastChild);
                }
            }
        };
        
        addThought();
        setInterval(addThought, 3000);
    }

    function simulateCognitiveEvent() {
        // Random emotion change
        Object.keys(initialEmotions).forEach(key => {
            initialEmotions[key] = Math.max(0, Math.min(100, initialEmotions[key] + (Math.random() - 0.5) * 10));
            initialEmotions[key] = Math.round(initialEmotions[key]);
        });
        
        updateEmotionBars(initialEmotions);
        
        // Randomly update radial charts
        Object.keys(influenceValues).forEach(key => {
            influenceValues[key] = Math.max(0, Math.min(100, influenceValues[key] + (Math.random() - 0.5) * 5));
        });
        drawRadialCharts();
    }

    // --- Event Handlers ---
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.section).classList.add('active');
            
            if (btn.dataset.section === 'graph') {
                setTimeout(drawKnowledgeGraph, 100);
            }
        });
    });

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderBeliefs();
        });
    });

    pillButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            pillButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedInputType = btn.dataset.type;
        });
    });

    emotionSliders.forEach(slider => {
        slider.addEventListener('input', (e) => {
            const valEl = document.getElementById(`${e.target.id}Val`);
            valEl.textContent = e.target.value;
        });
    });

    // History events
    historySearch.addEventListener('input', renderHistory);
    historyFilter.addEventListener('change', renderHistory);

    window.deleteHistoryItem = (id) => {
        inputHistory = inputHistory.filter(item => item.id !== id);
        localStorage.setItem('cognitiveMindHistory', JSON.stringify(inputHistory));
        renderHistory();
    };

    // Voice input
    let isListening = false;
    if ('webkitSpeechRecognition' in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';
        recognition.onstart = () => {
            isListening = true;
            micBtn.classList.add('listening');
        };
        recognition.onresult = (e) => {
            const transcript = e.results[0][0].transcript;
            cognitiveInput.value += transcript;
        };
        recognition.onend = () => {
            isListening = false;
            micBtn.classList.remove('listening');
        };
        recognition.onerror = () => {
            isListening = false;
            micBtn.classList.remove('listening');
        };
        
        micBtn.addEventListener('click', () => {
            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            submitInput();
        } else if (e.ctrlKey && e.key.toLowerCase() === 'l') {
            e.preventDefault();
            cognitiveInput.value = '';
        } else if (e.ctrlKey && e.key.toLowerCase() === 'h') {
            e.preventDefault();
            navButtons.forEach(b => b.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            document.querySelector('[data-section="history"]').classList.add('active');
            document.getElementById('history').classList.add('active');
        }
    });

    // Submit handler
    submitBtn.addEventListener('click', submitInput);

    function submitInput() {
        const text = cognitiveInput.value.trim();
        if (!text) return;
        
        processingFlow.style.display = 'flex';
        responsePanel.style.display = 'none';
        
        const flowSteps = processingFlow.querySelectorAll('.flow-step');
        let flowIndex = 0;
        
        const advanceFlow = () => {
            if (flowIndex > 0) {
                flowSteps[flowIndex -1].classList.remove('active');
                flowSteps[flowIndex -1].classList.add('completed');
            }
            if (flowIndex < flowSteps.length) {
                flowSteps[flowIndex].classList.add('active');
                flowIndex++;
                setTimeout(advanceFlow, 500);
            } else {
                // All steps complete, show response
                showResponse(text);
            }
        };
        advanceFlow();
        
        // Update emotion injection values
        Object.keys(initialEmotions).forEach(key => {
            const slider = document.getElementById(`slider${key.charAt(0).toUpperCase() + key.slice(1)}`);
            if (slider) {
                initialEmotions[key] = parseInt(slider.value);
            }
        });
        updateEmotionBars(initialEmotions);
        
        // Save to history
        const now = new Date();
        const impact = Math.floor(Math.random() * 60) + 20;
        inputHistory.unshift({
            id: crypto.randomUUID(),
            text,
            type: selectedInputType,
            impact,
            time: now.toLocaleTimeString()
        });
        localStorage.setItem('cognitiveMindHistory', JSON.stringify(inputHistory));
        renderHistory();
    }

    function showResponse(text) {
        processingFlow.style.display = 'none';
        responsePanel.style.display = 'block';
        
        // Update values for display
        document.getElementById('responseConcepts').textContent = extractConcepts(text);
        document.getElementById('responseBeliefs').textContent = 'Updating belief system based on input...';
        
        const updatedEmotions = Object.entries(initialEmotions)
            .filter(([k, v]) => v > 30)
            .map(([k, v]) => `${k.charAt(0).toUpperCase() + k.slice(1)}: ${v}%`)
            .join(', ');
        document.getElementById('responseEmotions').textContent = updatedEmotions;
        
        document.getElementById('responseMemory').textContent = 'Memory consolidated successfully';
        
        // Update influence
        Object.keys(influenceValues).forEach(key => {
            influenceValues[key] = Math.min(100, Math.max(0, influenceValues[key] + (Math.random() - 0.3) * 10));
        });
        drawRadialCharts();
        
        document.getElementById('responsePrediction').textContent = 'Cognitive state stabilizing; new goals forming';
        
        step++;
        updateDashboard({
            step,
            confidence: identityMetrics.confidence,
            stability: identityMetrics.consistency,
            energy: 60 + Math.floor(Math.random() * 30)
        });
    }

    function extractConcepts(text) {
        const common = ['work', 'sad', 'happy', 'fear', 'goal', 'belief', 'trust', 'memory', 'explore', 'learn'];
        const found = common.filter(word => text.toLowerCase().includes(word));
        if (found.length) {
            return found.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(', ');
        }
        return 'General cognitive input, analyzing...';
    }
});
