# Gameplay Recorder & Dream Engine

**PZBot** includes a suite of tools for recording human gameplay and processing those recordings to improve the bot's behavior. This allows us to "teach" the bot by example using "Dream Engine" processors.

## 1. Gameplay Recorder (`tools/recorder.py`)

A standalone tool that captures the game's state (from `state.json`) and saves it to a compressed recording file.

### Usage
1.  **Start the Game**: Launch Project Zomboid with the `AISurvivorBridge` mod enabled.
2.  **Run the Recorder**:
    ```powershell
    python tools/recorder.py
    ```
    *   *Optional Arguments*:
        *   `--state`: Path to `state.json` (default: auto-detected)
        *   `--output`: Directory to save recordings (default: `scenarios/recordings/`)
        *   `--lite`: **(Recommended)** Strip static tile data. Reduces file size by ~90%.

3.  **Play**: The recorder will capture frames in the background.
4.  **Bookmarks**:
    *   Type a label (e.g., "Combat Start") and press **ENTER** in the recorder console to add a bookmark.
    *   Use this to mark interesting events for training.
5.  **Stop**: Type `q` and press **ENTER** (or use Ctrl+C) to stop and save.

### Output
Files are saved to `scenarios/recordings/` as `gameplay_{TIMESTAMP}.jsonl.gz`.
*   **Format**: JSON Lines (Compressed).
*   **Content**: Raw dump of `state.json` frames + Bookmark metadata frames.

---

## 2. Dream Engine (`tools/dream/`)

The "Dream Engine" is a pipeline for processing recordings into usable configuration files or learning weights.

### Architecture
*   **Pipeline (`tools/dream/pipeline.py`)**: The runner script that loads recordings and executes processors.
*   **Processors (`tools/dream/processors/*.py`)**: Individual scripts that extract specific insights from the data.

### Running the Pipeline
```powershell
python tools/dream/pipeline.py scenarios/recordings/gameplay_20260101_120000.jsonl.gz
```
This will run ALL available processors on the specified recording.

### Creating New Processors
To add a new learning capability (e.g., "Learn safe paths"), create a new Python file in `tools/dream/processors/`.

**Example Template:**
```python
from tools.dream.lib.processor import RecordingProcessor

class MyNewProcessor(RecordingProcessor):
    def name(self):
        return "my_new_processor"

    def process(self, recording_path):
        data = {}
        # Iterate over frames
        for frame in self.stream_frames(recording_path):
            if "player" in frame:
                # Do analysis...
                pass
        
        # Save results
        self.save_artifact(data, "my_results.json", output_dir=self.config_dir)
        return data
```
