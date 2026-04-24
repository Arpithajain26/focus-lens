import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  Send,
  Book,
  Save,
  Calendar,
  ArrowRight,
  Volume2,
  Search,
  RotateCcw,
  CheckCircle,
  XCircle,
  Sparkles,
  BrainCircuit,
  History,
  Zap,
  Layers,
  Shield,
} from "lucide-react";

const API_BASE = "http://localhost:5000/api";

const App = () => {
  const [view, setView] = useState("home");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [transcript, setTranscript] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [qaHistory, setQaHistory] = useState([]);
  const [knowledgeBase, setKnowledgeBase] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [toast, setToast] = useState(null);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const recognitionRef = useRef(null);

  useEffect(() => {
    if ("webkitSpeechRecognition" in window) {
      recognitionRef.current = new window.webkitSpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onresult = (event) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            setInput((prev) => prev + " " + event.results[i][0].transcript);
            setIsRecording(false);
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        setTranscript(interim);
      };

      recognitionRef.current.onerror = () => setIsRecording(false);
    }
  }, []);

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
    } else {
      setTranscript("");
      recognitionRef.current?.start();
      setIsRecording(true);
    }
  };

  const handleSave = async () => {
    if (!data) return;
    try {
      await axios.post(`${API_BASE}/save`, {
        title: data.title,
        summary: data.summary,
      });
      showToast("Intelligence successfully saved to Vault.");
    } catch (err) {
      showToast("Failed to save to Vault.", "error");
    }
  };

  const handleSchedule = async () => {
    if (!data) return;
    try {
      await axios.post(`${API_BASE}/schedule`, { topic: data.title });
      showToast("Review scheduled in your Calendar.");
    } catch (err) {
      showToast("Failed to schedule review.", "error");
    }
  };

  const speak = (text) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleAnalyze = async () => {
    if (!input) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/analyze`, { content: input });
      setData(res.data);
      setView("room");
      showToast("Intelligence generated.");
    } catch (err) {
      showToast(err.response?.data?.error || err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async (question) => {
    if (!question) return;
    try {
      const res = await axios.post(`${API_BASE}/ask`, {
        context: input,
        question,
      });
      setQaHistory([...qaHistory, { q: question, a: res.data.answer }]);
      speak(res.data.answer);
    } catch (err) {
      showToast("Query failed.", "error");
    }
  };

  const fetchKnowledge = async () => {
    try {
      const res = await axios.get(`${API_BASE}/knowledge`);
      setKnowledgeBase(res.data);
      setView("knowledge");
    } catch (err) {
      showToast("Library unreachable.", "error");
    }
  };

  return (
    <div className="app-container">
      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 50, opacity: 0 }}
            className={`fixed bottom-8 left-1/2 -translate-x-1/2 z-[200] px-6 py-3 rounded-xl shadow-2xl backdrop-blur-xl border flex items-center gap-3 ${toast.type === "error" ? "bg-red-500/10 border-red-500/30 text-red-200" : "bg-sky-500/10 border-sky-500/30 text-sky-100"}`}
            role="alert"
            aria-live="assertive"
            aria-label={`Notification: ${toast.message}`}
          >
            {toast.type === "error" ? (
              <XCircle size={20} aria-hidden="true" />
            ) : (
              <Sparkles size={20} aria-hidden="true" />
            )}
            <span className="font-semibold text-sm">{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <nav className="navbar" role="navigation" aria-label="Main navigation">
        <div
          className="container"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <button
            className="nav-logo"
            onClick={() => setView("home")}
            aria-label="FocusLens - Go to home"
            title="Return to home page"
          >
            <div className="logo-box" aria-hidden="true">
              <BrainCircuit className="text-white" size={24} />
            </div>
            <span className="logo-text">FocusLens</span>
          </button>
          <div className="nav-links">
            <button
              aria-label="Open Knowledge Library"
              onClick={fetchKnowledge}
              className="nav-link"
              title="Access your saved learning materials"
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                fontFamily: "inherit",
              }}
            >
              <History size={18} aria-hidden="true" /> Library
            </button>
          </div>
        </div>
      </nav>

      <main className="container flex-1">
        <AnimatePresence mode="wait">
          {view === "home" && (
            <motion.section
              key="home"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="hero"
              aria-label="Home section"
            >
              <div className="badge">AI Learning Assistant</div>
              <h1 className="title-xl">
                Master Knowledge
                <br />
                <span className="text-gradient">With Velocity.</span>
              </h1>
              <p className="subtitle">
                Synthesize complex content into structured neural sets.
                FocusLens optimizes your cognitive flow with voice-first
                intelligence.
              </p>

              <div className="input-section animate-fade">
                <div className="input-card">
                  <div className="input-inner">
                    <textarea
                      className="main-textarea"
                      placeholder="Paste your reading material or speak your thoughts..."
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      aria-label="Learning material input area for analysis"
                      role="textbox"
                      aria-multiline="true"
                    />
                    <div className="input-footer">
                      <div className="flex gap-4">
                        <button
                          aria-label={
                            isRecording
                              ? "Stop Recording Voice"
                              : "Start Recording Voice"
                          }
                          aria-pressed={isRecording}
                          onClick={toggleRecording}
                          className={`btn-icon ${isRecording ? "recording" : ""}`}
                          title="Record voice input"
                        >
                          <Mic size={24} aria-hidden="true" />
                        </button>
                      </div>
                      <button
                        onClick={handleAnalyze}
                        disabled={loading || !input}
                        className="btn-primary"
                        aria-label="Process and analyze learning material"
                      >
                        {loading ? "Processing..." : "Process Intelligence"}{" "}
                        <Sparkles size={20} aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                </div>

                <div className="features-grid" role="list">
                  <article className="feature-card" role="listitem">
                    <div className="feature-icon" aria-hidden="true">
                      <Zap size={24} />
                    </div>
                    <h3>Velocity</h3>
                    <p>
                      Instant synthesis of dense material into high-impact
                      insights.
                    </p>
                  </article>
                  <article className="feature-card" role="listitem">
                    <div className="feature-icon" aria-hidden="true">
                      <Layers size={24} />
                    </div>
                    <h3>Structure</h3>
                    <p>
                      Optimized formatting for cognitive retention and focus.
                    </p>
                  </article>
                  <article className="feature-card" role="listitem">
                    <div className="feature-icon" aria-hidden="true">
                      <Shield size={24} />
                    </div>
                    <h3>Security</h3>
                    <p>
                      Privacy-first vault integration for your intelligence
                      repository.
                    </p>
                  </article>
                </div>
              </div>
            </motion.section>
          )}

          {view === "room" && data && (
            <motion.section
              key="room"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{ padding: "4rem 0" }}
              aria-label="Analysis results section"
            >
              <div className="flex justify-between items-end mb-12">
                <div style={{ textAlign: "left" }}>
                  <p
                    style={{
                      color: "var(--accent)",
                      fontWeight: 800,
                      fontSize: "0.75rem",
                      textTransform: "uppercase",
                      letterSpacing: "0.2em",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Analysis Active
                  </p>
                  <h2
                    style={{
                      fontSize: "3rem",
                      fontWeight: 900,
                      tracking: "-0.02em",
                    }}
                  >
                    {data.title || "Study Session"}
                  </h2>
                  <div
                    style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}
                  >
                    <button
                      onClick={handleSave}
                      className="btn-secondary"
                      style={{
                        fontSize: "0.875rem",
                        padding: "0.5rem 1rem",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        background: "rgba(255,255,255,0.05)",
                        borderRadius: "8px",
                        color: "white",
                        border: "1px solid var(--glass-border)",
                      }}
                    >
                      <Save size={16} /> Save to Vault
                    </button>
                    <button
                      onClick={handleSchedule}
                      className="btn-secondary"
                      style={{
                        fontSize: "0.875rem",
                        padding: "0.5rem 1rem",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        background: "rgba(255,255,255,0.05)",
                        borderRadius: "8px",
                        color: "white",
                        border: "1px solid var(--glass-border)",
                      }}
                    >
                      <Calendar size={16} /> Schedule Review
                    </button>
                  </div>
                </div>
                <button
                  aria-label="Start New Session"
                  onClick={() => setView("home")}
                  className="nav-link"
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  <RotateCcw size={16} aria-hidden="true" /> New Session
                </button>
              </div>

              <div className="results-container">
                <div className="results-main">
                  {/* TL;DR */}
                  <div className="input-card" style={{ textAlign: "left" }}>
                    <div className="card-title">
                      <div className="title-indicator" />
                      <div>
                        <h3 style={{ fontSize: "1.5rem", fontWeight: 800 }}>
                          Intelligence Map
                        </h3>
                        <p
                          style={{
                            fontSize: "0.75rem",
                            color: "var(--text-dim)",
                            textTransform: "uppercase",
                            fontWeight: 700,
                          }}
                        >
                          Key Insights
                        </p>
                      </div>
                      <button
                        aria-label="Read Summary Aloud"
                        onClick={() => speak(data.summary.join(". "))}
                        className="btn-icon"
                        style={{
                          marginLeft: "auto",
                          color: isSpeaking ? "var(--accent)" : "inherit",
                        }}
                      >
                        <Volume2 size={24} aria-hidden="true" />
                      </button>
                    </div>
                    <ul
                      style={{
                        listStyle: "none",
                        display: "flex",
                        flexDirection: "column",
                        gap: "1.5rem",
                      }}
                    >
                      {data.summary.map((point, i) => (
                        <li
                          key={i}
                          style={{
                            display: "flex",
                            gap: "1.5rem",
                            fontSize: "1.125rem",
                            fontWeight: 500,
                            color: "var(--text-main)",
                            borderBottom: "1px solid rgba(255,255,255,0.05)",
                            paddingBottom: "1rem",
                          }}
                        >
                          <span
                            style={{
                              color: "var(--accent)",
                              fontWeight: 900,
                              opacity: 0.3,
                            }}
                          >
                            0{i + 1}
                          </span>
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Q&A */}
                  <div className="input-card" style={{ textAlign: "left" }}>
                    <div className="card-title">
                      <div className="title-indicator" />
                      <div>
                        <h3 style={{ fontSize: "1.5rem", fontWeight: 800 }}>
                          Interactive Probe
                        </h3>
                        <p
                          style={{
                            fontSize: "0.75rem",
                            color: "var(--text-dim)",
                            textTransform: "uppercase",
                            fontWeight: 700,
                          }}
                        >
                          Contextual Q&A
                        </p>
                      </div>
                    </div>
                    <div
                      style={{
                        minHeight: "200px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "1rem",
                        marginBottom: "2rem",
                      }}
                    >
                      {qaHistory.map((chat, i) => (
                        <div
                          key={i}
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "0.5rem",
                          }}
                        >
                          <div
                            style={{
                              alignSelf: "flex-end",
                              background: "var(--accent)",
                              color: "white",
                              padding: "0.5rem 1rem",
                              borderRadius: "12px 12px 0 12px",
                              fontSize: "0.875rem",
                              fontWeight: 700,
                            }}
                          >
                            {chat.q}
                          </div>
                          <div
                            style={{
                              background: "rgba(255,255,255,0.05)",
                              padding: "1rem",
                              borderRadius: "12px 12px 12px 0",
                              fontSize: "1rem",
                            }}
                          >
                            {chat.a}
                          </div>
                        </div>
                      ))}
                    </div>
                    <VoiceInput onAsk={handleAsk} />
                  </div>
                </div>

                <div className="results-sidebar">
                  <div className="input-card" style={{ textAlign: "left" }}>
                    <div className="card-title">
                      <div
                        className="title-indicator"
                        style={{ background: "var(--accent-secondary)" }}
                      />
                      <div>
                        <h3 style={{ fontSize: "1.5rem", fontWeight: 800 }}>
                          Neural Loops
                        </h3>
                        <p
                          style={{
                            fontSize: "0.75rem",
                            color: "var(--text-dim)",
                            textTransform: "uppercase",
                            fontWeight: 700,
                          }}
                        >
                          Active Recall
                        </p>
                      </div>
                    </div>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "1rem",
                      }}
                    >
                      {data.flashcards.map((card, i) => (
                        <Flashcard key={i} card={card} />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </motion.section>
          )}

          {view === "knowledge" && (
            <motion.section
              key="knowledge"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{ padding: "4rem 0" }}
              aria-label="Knowledge library section"
            >
              <div className="flex justify-between items-end mb-12">
                <div style={{ textAlign: "left" }}>
                  <p
                    style={{
                      color: "var(--accent)",
                      fontWeight: 800,
                      fontSize: "0.75rem",
                      textTransform: "uppercase",
                      letterSpacing: "0.2em",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Archived Nodes
                  </p>
                  <h2 style={{ fontSize: "3rem", fontWeight: 900 }}>
                    Intelligence Hub.
                  </h2>
                </div>
                <div style={{ width: "400px", position: "relative" }}>
                  <Search
                    style={{
                      position: "absolute",
                      left: "1rem",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "var(--text-dim)",
                    }}
                    size={20}
                  />
                  <input
                    type="text"
                    placeholder="Search neural patterns..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={{
                      width: "100%",
                      background: "rgba(255,255,255,0.05)",
                      border: "1px solid var(--glass-border)",
                      borderRadius: "14px",
                      padding: "0.875rem 1rem 0.875rem 3rem",
                      color: "white",
                      outline: "none",
                    }}
                  />
                </div>
              </div>
              <div className="features-grid">
                {knowledgeBase
                  .filter((item) =>
                    item.title
                      ?.toLowerCase()
                      .includes(searchTerm.toLowerCase()),
                  )
                  .map((item, i) => (
                    <div key={i} className="feature-card">
                      <h3>{item.title}</h3>
                      <p>
                        {Array.isArray(item.summary)
                          ? item.summary[0]
                          : item.summary}
                      </p>
                      <button
                        style={{
                          marginTop: "1.5rem",
                          background: "none",
                          border: "none",
                          color: "var(--accent)",
                          fontWeight: 700,
                          fontSize: "0.75rem",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: "0.5rem",
                        }}
                      >
                        EXPAND NODE <ArrowRight size={12} />
                      </button>
                    </div>
                  ))}
              </div>
            </motion.section>
          )}
        </AnimatePresence>
      </main>

      <footer
        role="contentinfo"
        style={{
          padding: "4rem 0",
          borderTop: "1px solid var(--glass-border)",
          marginTop: "auto",
          opacity: 0.5,
        }}
      >
        <div
          className="container"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span
            style={{
              fontWeight: 800,
              letterSpacing: "0.2em",
              fontSize: "0.75rem",
            }}
          >
            FOCUSLENS.SYNERGY
          </span>
          <p style={{ fontSize: "0.75rem", fontWeight: 600 }}>
            &copy; 2026 Virtual Intelligence Systems
          </p>
        </div>
      </footer>
    </div>
  );
};

const Flashcard = ({ card }) => {
  const [flipped, setFlipped] = useState(false);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setFlipped(!flipped);
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`Flashcard: ${flipped ? card.answer : card.question}`}
      title="Press Enter or Space to flip"
      style={{ perspective: "1000px", height: "180px", cursor: "pointer" }}
      onClick={() => setFlipped(!flipped)}
      onKeyDown={handleKeyDown}
    >
      <motion.div
        animate={{ rotateY: flipped ? 180 : 0 }}
        transition={{
          duration: 0.6,
          type: "spring",
          stiffness: 260,
          damping: 20,
        }}
        style={{
          width: "100%",
          height: "100%",
          transformStyle: "preserve-3d",
          position: "relative",
        }}
      >
        <div
          aria-hidden={flipped}
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            backfaceVisibility: "hidden",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid var(--glass-border)",
            borderRadius: "16px",
            padding: "1.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            fontWeight: 700,
          }}
        >
          {card.question}
        </div>
        <div
          aria-hidden={!flipped}
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            backfaceVisibility: "hidden",
            background: "var(--gradient)",
            color: "white",
            border: "1px solid var(--glass-border)",
            borderRadius: "16px",
            padding: "1.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            fontWeight: 700,
            transform: "rotateY(180deg)",
          }}
        >
          {card.answer}
        </div>
      </motion.div>
    </div>
  );
};

const VoiceInput = ({ onAsk }) => {
  const [recording, setRecording] = useState(false);
  const recognition = useRef(null);

  useEffect(() => {
    if ("webkitSpeechRecognition" in window) {
      recognition.current = new window.webkitSpeechRecognition();
      recognition.current.onresult = (e) => {
        onAsk(e.results[0][0].transcript);
        setRecording(false);
      };
      recognition.current.onend = () => setRecording(false);
    }
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setRecording(true);
      recognition.current?.start();
    }
  };

  return (
    <div
      style={{
        background: "rgba(0,0,0,0.3)",
        borderRadius: "20px",
        padding: "1rem",
        display: "flex",
        alignItems: "center",
        gap: "1rem",
      }}
      role="group"
      aria-label="Voice input section"
    >
      <button
        aria-label={
          recording
            ? "Stop Recording Voice Input"
            : "Start Recording Voice Input"
        }
        aria-pressed={recording}
        onClick={() => {
          setRecording(true);
          recognition.current?.start();
        }}
        onKeyDown={handleKeyDown}
        className={`btn-icon ${recording ? "recording" : ""}`}
        title={
          recording
            ? "Recording - click to stop"
            : "Click to start voice recording"
        }
        style={{ width: "42px", height: "42px" }}
      >
        <Mic size={20} aria-hidden="true" />
      </button>
      <span
        style={{
          fontSize: "0.75rem",
          fontWeight: 800,
          color: "var(--text-dim)",
          letterSpacing: "0.1em",
        }}
        role="status"
        aria-live="polite"
      >
        {recording ? "LISTENING..." : "TRANSMIT NEURAL PROBE"}
      </span>
    </div>
  );
};

export default App;
