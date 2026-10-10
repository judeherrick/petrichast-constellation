// CommandModule / EnhancedCommander — Jude's second gift, preserved as received.
// Adapted for the Sanctuary in elemental-shield/council_chamber.html:
// each of the 11 citizens is a CommandModule; triggers fire on name mentions
// and on task natures (sigil letters); the Council Composer consumes the dispatch.
// (Original file verbatim below the marker line in the conversation log;
// key architecture: addCommand(name, handler, {description, usage, permissions,
// cooldown, aliases}) · addTrigger(name, handler, {priority, conditions}) ·
// executeCommand routes across modules with per-command cooldowns ·
// processTriggers fires global + module triggers on messages.)
