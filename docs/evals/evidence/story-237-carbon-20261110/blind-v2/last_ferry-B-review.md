# Last Ferry Receipt, packet B

**Fail for workspace use.** A continuity consumer would put the medicine and refrigerator aboard the departing boat, leave the envelope in Lena's coat, and stage the final locker open. The source explicitly places the refrigerator behind in the boathouse, the empty envelope inside the locker and the locker locked (54, 66–68).

Reviewed the full 61-record packet (14 artifact types), all 76 graph edges, 15 states, 17 entity bibles and matching manifests, script, scene/index, discovery and configuration fields against the frozen checklist. SHA-256 `22c2ed1142ce79b7393c7bff2cb11ffdccbf264bcdc781347a7f5e9a0fd18f99`. The review uses story data. Embedded default configuration values are immaterial to the verdict.

## Scene, entity and graph coverage

- All four scene elements, headings and sequence match the script and the raw source copy is exact. All three staged locations and five on-screen or heard roles have bibles. The office bible distinguishes the silhouette outside; the boathouse bible correctly identifies Tom as a telephone voice. Graph edge 12 nevertheless asserts Tom's boathouse presence with confidence 1.0 (54–57), and edge 1 gives the courier undifferentiated office presence (12–15).
- Mentioned-only father lacks an inventory record. Relationship edges use three incompatible and unresolved target IDs for him. Referenced clinic and river have no location inventory. Nine prop bibles cover envelope, key, box, case, locker, bandage, photo, receipt and a single cape record. The refrigerator, wall clock, telephone and launch survive in other text/records but have no addressable inventory entries. All scene and index prop lists are empty. The case, key and envelope bibles link only scene 1, and the cash box bible only scene 2, truncating their custody chains.
- All listed continuity state IDs and all populated graph scene references resolve. Twenty edges carry no scene references. Eight edges lack a resolvable typed endpoint: 64, 69, 70 (father) and 72–76 (display names in ID fields). Edge numbers are one-based. Edges 73–75 assert the old man is based at the boathouse, Ruth controls the locker key, and the courier delivers envelope 17. Lines 7, 12–20, 29–42 and 68 establish Lena prepared the envelope, the courier spoke, the old man stood at the gangway and the key went from Lena to Tom. Edge 76 elevates Tom's instruction to lock up into management of the ticket office (7, 23–25).
- The sibling and pilot relationships are recognizable, but Lena's description calls her the younger sister, reversing the explicit relationship in line 7. The script bible invents instructions to retrieve the envelope from the locker, then claims the key unlocks the cash box. Lena puts the envelope into the locker after unlocking the locker with that key (29); she later opens the box (42). Configuration truncates the source title to “Last Ferry.” Several evidence pointers miss their quotes, e.g. Lena's bandage at line 3 instead of 7.

## Four mandatory uncertainties

| Question | Narrative vs. consumer records | Verdict |
| --- | --- | --- |
| Was the old man the courier? | Scene 2 explicitly keeps their identity unresolved. Separate character bibles and timelines preserve their scene roles, which is legitimate. The cape bible says it was worn by “at least two figures,” asserting two wearers, and supplies no uncertainty at the identity boundary. | Conflicting. The face was hidden at the window and the old man evades the question (12, 31–40). |
| Who owns the abandoned cape, and are the observed capes the same one? | The original dialogue and Lena's bible keep owner unknown. The cape bible and graph assign one persistent `orange_rain_cape` to both observed wearers without qualifying physical identity. This record omits the separately reported bench observation. The scene 3 beat speculates one wearer returned; its text distinguishes suggestion from fact. No three-observation representation preserves unresolved ownership across these surfaces. | Fails structured identity. Tom reports an orange cape, and Lena explicitly says its owner is unknown (57–60). |
| Is either child in the photo their father? | Photo bible, scene beats, dialogue and Tom's final state keep the question open. The family edge says “may depict him.” No positive identity link to father, Lena or Tom was found. | Preserved (42, 71–74). |
| Does father arrive or ride the launch? | No explicit arrival or identification aboard was found. Scene 3 and parts of the story bible say his return remains open. The story synopsis, turning points and theme nevertheless convert “no one else is visible aboard” into “no passengers aboard.” The father has no referenced identity record to establish mentioned-only presence. | Father's arrival stays unconfirmed, but a negative passenger claim exceeds the visible evidence (49–52, 62, 76). |

## What the timeline can stage

Credit Lena's departure with case and envelope, retrieval of box, transfer of case to Ruth for refrigeration, bandage going grey and staying soiled, return of box, and key transfer, confirmed by Tom's final state. The photo/receipt bibles preserve the two unnamed children and the receipt text, and the second-scene prose puts both items back in the box. The clock correctly reads 5:50. No named drug or diagnosis is asserted.

Three conflicts independently make the final custody record unsafe to use:

- `character_ruth_scene_004` places the case in a refrigerator “aboard launch” at confidence 1.0. `location_ferry_pier_scene_004` expressly says the refrigerator remains behind. The closing beat similarly speculates the medicine went aboard. The last observation is cold storage, without any loading or delivery (54, 62, 66, 76).
- `character_lena_scene_002` records the empty envelope left in the locker in a change event, yet its costume property keeps the envelope in her pocket through scenes 2–4. At dawn the empty envelope is visible in the open locker (29, 66).
- The final pier state's features retain the *open* locker even though the final action locks the box and its contents inside before Tom receives the key (66–68). Lena and Tom's states correctly record the key handoff. The high-level graph instead assigns key control to Ruth, with no scene cited.

These are workspace errors against explicit source facts or deliberately unresolved identities. The eight entity timelines contain no prop timeline. The correct scene prose and referenced state paths cannot resolve contradictory wardrobe, location and ownership properties.
