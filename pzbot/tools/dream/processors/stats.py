from tools.dream.lib.processor import RecordingProcessor
import json
import sys

class StatsProcessor(RecordingProcessor):
    def name(self):
        return "stats"

    def process(self, recording_path):
        self.logger.info(f"Analyzing sizes in {recording_path.name}...")
        
        total_size = 0
        frame_count = 0
        key_usage = {}
        
        # We need raw line access to check uncompressed size, 
        # but stream_frames gives us dicts.
        # We'll re-serialize to estimate raw size cost.
        
        for frame in self.stream_frames(recording_path):
            frame_count += 1
            raw = json.dumps(frame)
            size = len(raw)
            total_size += size
            
            # recursive size check for top-level keys
            if "state" in frame:
                state = frame["state"]
                if "player" in state:
                    p = state["player"]
                    if "vision" in p:
                        v = p["vision"]
                        for k, val in v.items():
                            sz = len(json.dumps(val))
                            key_usage[f"vision.{k}"] = key_usage.get(f"vision.{k}", 0) + sz
            
            if frame_count > 100: break # Sample first 100 frames is enough
            
        if frame_count == 0: return None
        
        avg_frame = total_size / frame_count
        self.logger.info(f"Avg Raw Frame Size: {avg_frame/1024:.2f} KB")
        self.logger.info("Top Consumers (Approx Bytes per frame):")
        
        sorted_keys = sorted(key_usage.items(), key=lambda x: x[1], reverse=True)
        for k, v in sorted_keys:
            avg_k = v / frame_count
            pct = (avg_k / avg_frame) * 100
            self.logger.info(f"  - {k}: {avg_k/1024:.2f} KB ({pct:.1f}%)")
            
        return {"avg_size": avg_frame}
