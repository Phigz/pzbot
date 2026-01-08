import sys
import argparse
import logging
import importlib.util
from pathlib import Path
from typing import List

# Setup paths
CURRENT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = CURRENT_DIR.parent.parent
PROCESSORS_DIR = CURRENT_DIR / "processors"

sys.path.append(str(ROOT_DIR))
from tools.dream.lib.processor import RecordingProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DreamPipeline")

def load_processors() -> List[RecordingProcessor]:
    processors = []
    if not PROCESSORS_DIR.exists():
        PROCESSORS_DIR.mkdir(parents=True)
        return []

    for file_path in PROCESSORS_DIR.glob("*.py"):
        if file_path.name == "__init__.py": continue
        
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find subclasses
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, RecordingProcessor) and attr is not RecordingProcessor:
                    processors.append(attr())
                    logger.info(f"Loaded processor: {attr_name}")
    
    return processors

def run_pipeline(recording_path: Path):
    logger.info(f"Running pipeline on {recording_path.name}...")
    
    processors = load_processors()
    if not processors:
        logger.warning("No processors found in tools/dream/processors/")
        return

    for proc in processors:
        try:
            logger.info(f"Running {proc.name()}...")
            result = proc.process(recording_path)
            if result:
               logger.info(f"Processor {proc.name()} completed successfully.")
            else:
               logger.info(f"Processor {proc.name()} returned no data (skipped?).")
        except Exception as e:
            logger.error(f"Processor {proc.name()} failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Dream Engine Pipeline Runner")
    parser.add_argument("recording", type=str, help="Path to .jsonl.gz recording file")
    args = parser.parse_args()
    
    path = Path(args.recording)
    if not path.exists():
        logger.error(f"File not found: {path}")
        return
        
    run_pipeline(path)

if __name__ == "__main__":
    main()
