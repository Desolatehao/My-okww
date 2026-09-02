# My-okww Workspace

This top-level folder is the user's private working repository. It contains two separate project checkouts:

- `ok-wuthering-waves`: the original upstream checkout, kept at its original commit and with its original Git metadata.
- `ok-wuthering-waves-custom`: the working copy for the Douling/Phrolova/Verina axis, including the modified source files and `axis_douling_phrolova_verina/` notes.

Do not edit or commit changes directly in `ok-wuthering-waves`. Future character-axis work belongs in `ok-wuthering-waves-custom` and its `axis_douling_phrolova_verina/` documentation folder.

The exact team gate is `char_douling`, `char_phrolova`, and `char_verina`. The custom state machine is task-level (`_dpv_axis_state`) and leaves other teams on their original character logic. `Verina C2` is configured in the customized checkout's `config.py`; set it to true only for an actual C2 Verina.

The three customized character files are:

- `ok-wuthering-waves-custom/src/char/Douling.py`
- `ok-wuthering-waves-custom/src/char/Phrolova.py`
- `ok-wuthering-waves-custom/src/char/Verina.py`

The loose copies in `ok-wuthering-waves-custom/axis_douling_phrolova_verina/` are the review snapshot. The historical `弗卜维.zip` is retained and is not assumed to contain a current `team.json` importer manifest.

Static validation is available with the customized checkout's Python environment if dependencies are installed. Full in-game validation remains outstanding and should be done against a low-risk target before tuning timings.
