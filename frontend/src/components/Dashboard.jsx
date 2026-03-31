// import React, { useState, useRef, useEffect } from 'react';
// import axios from 'axios';
// import ReactMarkdown from 'react-markdown';
// import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
// import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
// import './Dashboard.css'; // Humari nayi styling!

// function Dashboard({ onLogout }) {
//   const [repoUrl, setRepoUrl] = useState('');
//   const [question, setQuestion] = useState('');
//   const [chatHistory, setChatHistory] = useState([]);
//   const [isSyncing, setIsSyncing] = useState(false);
//   const [isAsking, setIsAsking] = useState(false);
//   const [repoData, setRepoData] = useState({ owner: '', repo: '' });
//   const messagesEndRef = useRef(null);

//   // Auto-scroll chat to bottom
//   const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   useEffect(() => scrollToBottom(), [chatHistory, isAsking]);

//   const getAuthHeader = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });

//   // 1. Process Repo Logic
//   const handleProcessRepo = async () => {
//     if (!repoUrl.includes('github.com')) return alert("Please enter a valid GitHub URL.");
//     try {
//       setIsSyncing(true);
//       const urlParts = repoUrl.replace(/\/$/, '').split('/');
//       const repo = urlParts.pop();
//       const owner = urlParts.pop();
//       setRepoData({ owner, repo });

//       const res = await axios.post('http://127.0.0.1:8000/process', { owner, repo }, getAuthHeader());
//       alert("✅ " + res.data.message);
//     } catch (error) {
//       alert("❌ Error processing repo. Please check the URL or your connection.");
//     } finally {
//       setIsSyncing(false);
//     }
//   };

//   // 2. Generate README Logic
//   const handleGenerateReadme = async () => {
//     if (!repoData.repo) return alert("Please Process a repository first!");
//     setChatHistory(prev => [...prev, { role: 'user', content: 'Generate a professional README for this project.' }]);
//     setIsAsking(true);
//     try {
//       const res = await axios.post('http://127.0.0.1:8000/readme', { owner: repoData.owner, repo: repoData.repo }, getAuthHeader());
//       setChatHistory(prev => [...prev, { role: 'ai', content: res.data.readme }]);
//     } catch (error) {
//       setChatHistory(prev => [...prev, { role: 'ai', content: "❌ Error generating README." }]);
//     } finally {
//       setIsAsking(false);
//     }
//   };

//   // 3. Ask Question Logic
//   const handleAskQuestion = async () => {
//     if (!question || !repoData.owner) return;
//     const userMsg = { role: 'user', content: question };
//     setChatHistory(prev => [...prev, userMsg]);
//     setQuestion('');
//     setIsAsking(true);

//     try {
//       const res = await axios.post('http://127.0.0.1:8000/chat', { owner: repoData.owner, repo: repoData.repo, question: userMsg.content }, getAuthHeader());
//       setChatHistory(prev => [...prev, { role: 'ai', content: res.data.answer }]);
//     } catch (error) {
//       setChatHistory(prev => [...prev, { role: 'ai', content: "❌ Error getting answer." }]);
//     } finally {
//       setIsAsking(false);
//     }
//   };

//   return (
//     <div className="dashboard-wrapper">
//       <div className="dashboard-container">
        
//         {/* TOP BAR */}
//         <div className="top-nav">
//           <h2>Codebase AI <span style={{fontSize:'14px', color:'#94a3b8', fontWeight:'normal'}}>| {localStorage.getItem('username')}</span></h2>
//           <button onClick={onLogout} className="logout-btn">Log Out</button>
//         </div>

//         {/* CONTROLS (URL + Process + Readme) */}
//         <div className="controls-section">
//           <input 
//             type="text" 
//             className="repo-input" 
//             placeholder="Paste GitHub URL (e.g., https://github.com/facebook/react)" 
//             value={repoUrl} 
//             onChange={(e) => setRepoUrl(e.target.value)} 
//           />
//           <button onClick={handleProcessRepo} disabled={isSyncing} className="btn-process">
//             {isSyncing ? "⏳ Processing..." : "⚙️ Process Repo"}
//           </button>
//           <button onClick={handleGenerateReadme} disabled={!repoData.repo || isAsking} className="btn-readme">
//             📄 Generate README
//           </button>
//         </div>

//         {/* CHAT INTERFACE */}
//         <div className="chat-section">
          
//           {/* Messages Area */}
//           <div className="chat-history">
//             {chatHistory.length === 0 ? (
//               <div style={{ margin: 'auto', textAlign: 'center', color: '#64748b' }}>
//                 <h3>Welcome to the Workspace</h3>
//                 <p>Process a repository above to start exploring the codebase.</p>
//               </div>
//             ) : null}
            
//             {chatHistory.map((msg, idx) => (
//               <div key={idx} className={`message-row ${msg.role}`}>
//                 <div className={`message-bubble ${msg.role}`}>
//                   <ReactMarkdown 
//                     components={{ 
//                       code({node, inline, className, children, ...props}) { 
//                         const match = /language-(\w+)/.exec(className || ''); 
//                         return !inline && match ? ( 
//                           <SyntaxHighlighter style={vscDarkPlus} language={match[1]} PreTag="div" {...props}>
//                             {String(children).replace(/\n$/, '')}
//                           </SyntaxHighlighter> 
//                         ) : ( 
//                           <code style={{background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: '4px'}} {...props}>{children}</code> 
//                         ) 
//                       } 
//                     }}
//                   >
//                     {msg.content}
//                   </ReactMarkdown>
//                 </div>
//               </div>
//             ))}
//             {isAsking && (
//               <div className="message-row ai">
//                 <div className="message-bubble ai" style={{ opacity: 0.7 }}>🤖 Analyzing codebase...</div>
//               </div>
//             )}
//             <div ref={messagesEndRef} />
//           </div>

//           {/* Input Area (Bottom) */}
//           <div className="chat-input-area">
//             <input 
//               type="text" 
//               className="chat-input" 
//               placeholder={repoData.repo ? `Ask a question about ${repoData.repo}...` : "Process a repo first..."} 
//               value={question} 
//               onChange={(e) => setQuestion(e.target.value)} 
//               onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()} 
//               disabled={!repoData.repo || isAsking} 
//             />
//             <button onClick={handleAskQuestion} disabled={!repoData.repo || isAsking || !question} className="btn-send">
//               ➤ Send
//             </button>
//           </div>

//         </div>

//       </div>
//     </div>
//   );
// }

// export default Dashboard;





import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './Dashboard.css'; 

function Dashboard({ onLogout }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isAsking, setIsAsking] = useState(false);
  const [repoData, setRepoData] = useState({ owner: '', repo: '' });
  
  // 🌟 NAYA: isSyncing ko hata kar syncStatus laga diya
  const [syncStatus, setSyncStatus] = useState('idle'); // 'idle', 'syncing', 'synced'
  
  const messagesEndRef = useRef(null);

  // Auto-scroll chat to bottom
  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => scrollToBottom(), [chatHistory, isAsking]);

  const getAuthHeader = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });

  // 1. Process Repo Logic (SMART PARSER)
  const handleProcessRepo = async () => {
    if (!repoUrl.includes('github.com')) return alert("Please enter a valid GitHub URL.");
    
    try {
      setSyncStatus('syncing'); 
      
      const urlObj = new URL(repoUrl);
      const pathParts = urlObj.pathname.split('/').filter(Boolean);
      
      if (pathParts.length < 2) {
        setSyncStatus('idle');
        return alert("URL mein owner aur repo missing hai!");
      }

      const owner = pathParts[0]; 
      const repo = pathParts[1];  
      setRepoData({ owner, repo });

      const res = await axios.post('http://127.0.0.1:8000/process', { owner, repo }, getAuthHeader());
      
      setSyncStatus('synced'); 
      alert("✅ " + res.data.message);
    } catch (error) {
      setSyncStatus('idle'); 
      alert("❌ Error processing repo. Please check the console or URL.");
      console.error(error);
    }
  };

  // 2. Generate README Logic
  const handleGenerateReadme = async () => {
    if (!repoData.repo) return alert("Please Process a repository first!");
    setChatHistory(prev => [...prev, { role: 'user', content: 'Generate a professional README for this project.' }]);
    setIsAsking(true);
    try {
      const res = await axios.post('http://127.0.0.1:8000/readme', { owner: repoData.owner, repo: repoData.repo }, getAuthHeader());
      setChatHistory(prev => [...prev, { role: 'ai', content: res.data.readme }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: 'ai', content: "❌ Error generating README." }]);
    } finally {
      setIsAsking(false);
    }
  };

  // 3. Ask Question Logic
  const handleAskQuestion = async () => {
    if (!question || !repoData.owner) return;
    const userMsg = { role: 'user', content: question };
    setChatHistory(prev => [...prev, userMsg]);
    setQuestion('');
    setIsAsking(true);

    try {
      const res = await axios.post('http://127.0.0.1:8000/chat', { owner: repoData.owner, repo: repoData.repo, question: userMsg.content }, getAuthHeader());
      setChatHistory(prev => [...prev, { role: 'ai', content: res.data.answer }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: 'ai', content: "❌ Error getting answer." }]);
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="dashboard-wrapper">
      <div className="dashboard-container">
        
        {/* TOP BAR */}
        <div className="top-nav">
          <h2>Codebase AI <span style={{fontSize:'14px', color:'#94a3b8', fontWeight:'normal'}}>| {localStorage.getItem('username')}</span></h2>
          <button onClick={onLogout} className="btn-premium logout-btn">Log Out</button>
        </div>

        {/* CONTROLS (URL + Process + Readme) */}
        <div className="controls-section">
          <input 
            type="text" 
            className="repo-input" 
            placeholder="Paste GitHub URL (e.g., https://github.com/facebook/react)" 
            value={repoUrl} 
            onChange={(e) => {
              setRepoUrl(e.target.value);
              setSyncStatus('idle'); // Naya URL type karte hi button wapas Orange ho jayega
            }} 
          />
          
          <button 
            onClick={handleProcessRepo} 
            disabled={syncStatus === 'syncing'} 
            className="btn-premium"
            style={syncStatus === 'synced' ? { background: 'linear-gradient(90deg, #10b981, #059669)' } : {}}
          >
            {syncStatus === 'syncing' ? "⏳ Processing..." : 
             syncStatus === 'synced' ? "🔄 Re-Process" : 
             <><i className="fa fa-cog"></i> Process Repo</>}
          </button>

          <button onClick={handleGenerateReadme} disabled={!repoData.repo || isAsking} className="btn-premium">
            📄 Generate README
          </button>
        </div>

        {/* CHAT INTERFACE */}
        <div className="chat-section">
          
          {/* Messages Area */}
          <div className="chat-history">
            {chatHistory.length === 0 ? (
              <div style={{ margin: 'auto', textAlign: 'center', color: '#64748b' }}>
                <h3>Welcome to the Workspace</h3>
                <p>Process a repository above to start exploring the codebase.</p>
              </div>
            ) : null}
            
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={`message-row ${msg.role}`}>
                <div className={`message-bubble ${msg.role}`}>
                  <ReactMarkdown 
                    components={{ 
                      code({node, inline, className, children, ...props}) { 
                        const match = /language-(\w+)/.exec(className || ''); 
                        return !inline && match ? ( 
                          <SyntaxHighlighter style={vscDarkPlus} language={match[1]} PreTag="div" {...props}>
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter> 
                        ) : ( 
                          <code style={{background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px'}} {...props}>{children}</code> 
                        ) 
                      } 
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
            {isAsking && (
              <div className="message-row ai">
                <div className="message-bubble ai" style={{ opacity: 0.7 }}>🤖 Analyzing codebase...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area (Bottom) */}
          <div className="chat-input-area">
            <input 
              type="text" 
              className="chat-input" 
              placeholder={repoData.repo ? `Ask a question about ${repoData.repo}...` : "Process a repo first..."} 
              value={question} 
              onChange={(e) => setQuestion(e.target.value)} 
              onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()} 
              disabled={!repoData.repo || isAsking} 
            />
            <button onClick={handleAskQuestion} disabled={!repoData.repo || isAsking || !question} className="btn-premium btn-send">
              ➤ Send
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}

export default Dashboard;