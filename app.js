// --- OLD (Delete this) ---
// import CoverArtWizard from './components/CoverArtWizard';

// --- NEW (Use this) ---
import CoverArtWizard from './CoverArtWizard'; // <--- Note: No "/components/"

function App() {
  return (
    <div className="App">
      <h1 style={{ textAlign: 'center' }}>My Cover Art Tool</h1>
      <CoverArtWizard />
    </div>
  );
}

export default App;
