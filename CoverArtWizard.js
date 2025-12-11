import React, { useState, useEffect } from 'react';

// --- CONSTANTS ---
const STEPS = {
  UPLOAD: 0,
  ANALYSIS: 1, // This is where you were getting stuck
  METADATA: 2,
  REVIEW: 3
};

// --- MAIN COMPONENT ---
export default function CoverArtWizard() {
  const [currentStep, setCurrentStep] = useState(STEPS.UPLOAD);
  
  // This holds ALL your data for the final review
  const [wizardData, setWizardData] = useState({
    originalImage: null,
    processedImage: null,
    artist: '',
    track: '',
    genre: ''
  });

  // Helper to update state
  const updateData = (key, value) => {
    setWizardData(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      
      {/* PROGRESS BAR */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
        {Object.keys(STEPS).map((stepName, index) => (
          <div key={stepName} style={{ fontWeight: currentStep === index ? 'bold' : 'normal', color: currentStep === index ? 'blue' : '#ccc' }}>
            {stepName}
          </div>
        ))}
      </div>

      <hr />

      {/* --- STEP 1: UPLOAD --- */}
      {currentStep === STEPS.UPLOAD && (
        <div className="step-container">
          <h2>1. Upload Cover Art</h2>
          <input 
            type="file" 
            onChange={(e) => {
              if(e.target.files[0]) {
                updateData('originalImage', URL.createObjectURL(e.target.files[0]));
                setCurrentStep(STEPS.ANALYSIS); // Auto-advance
              }
            }} 
          />
        </div>
      )}

      {/* --- STEP 2: ANALYSIS & FIX (THE PROBLEM AREA) --- */}
      {currentStep === STEPS.ANALYSIS && (
        <AnalysisStep 
          image={wizardData.originalImage}
          onFixComplete={(fixedImageUrl) => {
            updateData('processedImage', fixedImageUrl);
            // We DO NOT auto-advance here to let user see the result, 
            // instead we enable the 'Next' button inside the component.
          }}
          onNext={() => setCurrentStep(STEPS.METADATA)}
          onBack={() => setCurrentStep(STEPS.UPLOAD)}
        />
      )}

      {/* --- STEP 3: METADATA --- */}
      {currentStep === STEPS.METADATA && (
        <div className="step-container">
          <h2>3. Edit Details</h2>
          <p>AI found this data (Mocked):</p>
          
          <label style={{display: 'block', marginTop: '10px'}}>Artist:</label>
          <input 
            value={wizardData.artist} 
            onChange={(e) => updateData('artist', e.target.value)} 
            placeholder="Enter Artist Name"
            style={{ width: '100%', padding: '8px' }}
          />

          <label style={{display: 'block', marginTop: '10px'}}>Track Title:</label>
          <input 
            value={wizardData.track} 
            onChange={(e) => updateData('track', e.target.value)} 
            placeholder="Enter Track Title"
            style={{ width: '100%', padding: '8px' }}
          />

          <div style={{ marginTop: '20px' }}>
            <button onClick={() => setCurrentStep(STEPS.ANALYSIS)}>Back</button>
            <button 
              onClick={() => setCurrentStep(STEPS.REVIEW)} 
              style={{ marginLeft: '10px', backgroundColor: 'blue', color: 'white' }}
            >
              Review Final ›
            </button>
          </div>
        </div>
      )}

      {/* --- STEP 4: FINAL REVIEW --- */}
      {currentStep === STEPS.REVIEW && (
        <div className="step-container">
          <h2>4. Final Review</h2>
          
          <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', gap: '20px' }}>
              <img 
                src={wizardData.processedImage || wizardData.originalImage} 
                alt="Final" 
                style={{ width: '100px', height: '100px', objectFit: 'cover' }} 
              />
              <div>
                <h3>{wizardData.track || "Untitled Track"}</h3>
                <p>{wizardData.artist || "Unknown Artist"}</p>
              </div>
            </div>
            
            <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button onClick={() => setCurrentStep(STEPS.ANALYSIS)}>Edit Artwork</button>
              <button onClick={() => setCurrentStep(STEPS.METADATA)}>Edit Text</button>
            </div>
          </div>

          <button 
            style={{ marginTop: '20px', width: '100%', padding: '15px', backgroundColor: 'green', color: 'white', fontSize: '1.2em' }}
            onClick={() => alert("Success! Sent to distribution.")}
          >
            Submit Release
          </button>
        </div>
      )}
    </div>
  );
}

// --- SUB-COMPONENT: HANDLES THE FIXING LOGIC ---
function AnalysisStep({ image, onFixComplete, onNext, onBack }) {
  const [status, setStatus] = useState('idle'); // idle, processing, done

  const handleFix = () => {
    setStatus('processing');
    
    // MOCK AI DELAY
    setTimeout(() => {
      setStatus('done');
      // Pass the "fixed" image up to the parent
      onFixComplete(image); 
    }, 2000);
  };

  return (
    <div className="step-container">
      <h2>2. Analyze & Fix</h2>
      
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        <img src={image} alt="Original" style={{ maxWidth: '200px', borderRadius: '8px' }} />
      </div>

      {status === 'idle' && (
        <div>
          <p>AI detected text on your cover. Remove it?</p>
          <button onClick={handleFix} style={{ padding: '10px 20px', backgroundColor: 'purple', color: 'white' }}>
            ✨ Remove Text with AI
          </button>
          <br/><br/>
          <button onClick={onBack} style={{ color: '#666' }}>Back</button>
        </div>
      )}

      {status === 'processing' && (
        <div>
          <p>🎨 AI is painting over the text...</p>
          {/* Simple Spinner */}
          <div style={{ width: '20px', height: '20px', border: '3px solid #ccc', borderTop: '3px solid blue', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto' }}></div>
        </div>
      )}

      {status === 'done' && (
        <div>
          <p style={{ color: 'green' }}>✅ Text Removed!</p>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
            <button onClick={handleFix}>Retry</button>
            {/* THIS IS THE BUTTON THAT LETS YOU CONTINUE */}
            <button onClick={onNext} style={{ backgroundColor: 'blue', color: 'white', padding: '10px 20px' }}>
              Next Step ›
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
