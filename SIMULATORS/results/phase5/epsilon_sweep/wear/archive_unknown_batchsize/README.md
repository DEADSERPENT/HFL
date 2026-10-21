Archived 2026-09-08. These 12 rows (full + head, 6 eps each) were written
2026-08-05. Their --batch_size is UNRECOVERABLE: the original run log was
overwritten on 2026-09-06 by a --resume run that skipped all 12 combinations
and therefore recorded its own flags without computing anything.

They are archived rather than deleted, but they are NOT the authoritative
table: mixing them with B7 full_pre rows computed at batch 64 would leave a
reviewer unable to rule out batch size as the cause of the B4->B7 gap, which
is the exact effect the experiment isolates.

The authoritative wear sweep is the sibling epsilon_sweep.csv, recomputed in
full (18 points: full / full_pre / head x 6 eps) at batch_size 64.
