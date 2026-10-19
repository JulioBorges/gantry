# Host-only setup repair CLI evidence

This is deterministic public CLI evidence from temporary Git repositories. It proves policy and
adapter proposal/application behavior. It is not automatic invocation detection or live hook
compatibility evidence. No adopting repository, real host adapter or tracked policy was mutated.
Automated stdin below models operator answers only inside the temporary fixture; it is not permission
to supply approval on an operator's behalf during actual setup.

Reproduce from the repository root:

```bash
python3 docs/evidence/host-harness-resolution/setup-repair-transcript.py
python3 -m unittest tests.test_host_setup_repair tests.test_gantry_setup tests.test_role_execution_defaults tests.test_guard_hook_wiring -v
```

The reproduction script uses only standard library subprocess argument arrays and isolated temporary
Git repositories. All policy text, including shell metacharacters, stays data. It asserts exact
policy bytes outside the changed host value, full role/custom field preservation, unrelated user hook
commands, unchanged other adapter bytes, no shell execution, safe cancellation and idempotence.
Additional public CLI tests exercise base and derived roles, malformed policy/adapters, duplicate
JSON keys, unsupported and unresolved identities, CRLF/Unicode formatting, normal setup approval for
missing policy, structured config-file input, and recording-only versus explicit denial decisions.
