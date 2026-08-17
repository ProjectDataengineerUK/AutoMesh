# Checkpoint recovery

Read the last committed cursor and compare it with the source watermark. Replay from the committed cursor; do not advance it before all effects are durable. Verify no-loss and document expected duplicate handling.
