# License Decision Memo

This memo is engineering guidance, not legal advice. No license has been selected and no formal `LICENSE` file was created.

## MIT

MIT is short, permissive, and widely understood. It permits broad reuse subject principally to retaining the copyright and license notice. Its simplicity often suits a small general-purpose utility.

## Apache-2.0

Apache-2.0 is also permissive but has more detailed terms, including an explicit patent grant and patent-termination provisions. Those details can be useful for a reusable research-infrastructure tool intended for longer-term collaboration and contributions.

## Evidence and recommendation

The implementation is a clean-room engineering project. The release audit found no migrated archived data, paper material, results, or inherited repository history. No third-party licensing blocker was identified in the local dependency and source inventory.

The engineering recommendation is `Apache-2.0` because explicit patent and contribution terms may better fit long-term collaborative infrastructure. This is not a claim that Apache-2.0 is legally superior. MIT remains a reasonable simpler option.

The user must choose MIT or Apache-2.0. Until that decision is made and the corresponding license/copyright details are reviewed, GitHub publication, tagging, release creation, and package-index publication remain blocked.
