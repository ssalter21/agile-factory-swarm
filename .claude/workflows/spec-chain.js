export const meta = {
  name: 'spec-chain',
  description: 'Turn the brief in the run directory into an approvable spec (constitution \u00a710)',
  whenToUse: 'Runs the five passes of \u00a710. Invoked only by the /spec-swarm skill, which owns the blackboard writes and the seam.',
  phases: [
    { title: 'Sweep', detail: 'researcher answers the opening questions' },
    { title: 'Draft', detail: 'voices draft independently, unseen by each other' },
    { title: 'Critique', detail: 'every voice reads every draft' },
    { title: 'Rebut', detail: 'each voice answers the critiques of its own draft' },
    { title: 'Synthesis', detail: 'spec writer merges the debate into the run directory' },
  ],
}

// ---------------------------------------------------------------------------
// The blackboard. This script has no filesystem access; every path below is an
// instruction to an agent. The /spec-swarm skill has already guaranteed the run
// directory exists with brief.md in it, and has read .swarm/spec.yaml for us.
// ---------------------------------------------------------------------------

const RUN = '.swarm/runs/current'
// Hidden, because the human's first sight of the run directory should not be twelve files
// that are not for them (section 11). A blocked run still resumes over its own drafts.
const WORK = RUN + '/.work'

// Three invocations, told apart by the skill from what is on disk (section 10):
//   fresh   the whole chain
//   resume  critique -> rebut -> synthesis over drafts that already exist
//   fold    the spec writer alone, writing the human's seam answers into a finished spec
const mode = (args && args.mode) || 'fresh'

// A resume re-enters at critique over drafts that already exist. Two things send a run
// there and they are not the same: a human answering a blocked run's questions, and a run
// that stopped for budget with nothing to answer (section 12). Only the first has answers
// to read, so the skill says which this is; a resume that does not say is the old one.
const hasAnswers = mode === 'resume' && !(args && args.answers === false)
const voices = (args && args.voices) || ['agile-agent', 'user-voice', 'domain-modeller', 'devils-advocate']

const LAW = [
  'You are bound by swarm/constitution.md. Read it before you act: \u00a710 places you in the spec swarm,',
  '\u00a75 is the question ladder, \u00a711 is the seam.',
  'Read ' + RUN + '/brief.md and .swarm/spec.yaml first. The brief is what was asked for; spec.yaml',
  'says who the user is and what the domain is.',
  'Write your output to the file named below, and return ONLY a terse pointer to it plus your',
  'headline. Never return the file contents. Your return value is machinery, not a message.',
].join('\n')

const RULING = {
  type: 'object',
  additionalProperties: false,
  required: ['verdict', 'settled', 'assumed', 'questions', 'why'],
  properties: {
    verdict: {
      type: 'string',
      enum: ['continue', 'block', 'restart'],
      description: 'continue: assumptions cover the gaps. block: a question no assumption is safe for. restart: a human answer broke a premise, so drafting must happen again.',
    },
    settled: { type: 'array', items: { type: 'string' }, description: 'questions research answered' },
    assumed: { type: 'array', items: { type: 'string' }, description: 'each assumption, then its cost if wrong' },
    why: { type: 'string', description: 'if blocking, why no assumption was safe. \u00a75 requires this.' },
    chosen: {
      type: 'array',
      items: { type: 'string' },
      description: 'disputed points you ruled on because being wrong is cheap. Each: the point, the side you took, whether a voice won the argument or you picked, and the cost if wrong. \u00a75 makes this yours; the spec writer never adjudicates.',
    },
    // ONE field for everything the human is asked, whichever gap emits it. There used to
    // be two -- `blocking` for a gap that ends the run, `questions` for the batch at the
    // seam -- and the \u00a711 shape rules only ever reached the second. So a run that blocked
    // early emitted the exact unstructured wall of prose \u00a711 exists to prevent. Two fields
    // meaning "questions for the human" will always drift apart; one cannot.
    questions: {
      type: 'array',
      maxItems: 8,
      items: { type: 'string' },
      description: 'everything the human is asked, each the FULL text of one question in \u00a711 shape: title, the fork as named options, what changes down each branch, the cost if wrong, and a recommendation ONLY where a voice won the argument (none where they were tied, and say so). At most three; if you exceed three, say for each extra one why the ladder failed. Under 40 lines each. Empty when the human needs to be asked nothing \u2014 which is required when the verdict is continue, and forbidden when it is block.',
    },
    research: {
      type: 'array',
      items: { type: 'string' },
      description: 'named questions to send to the researcher before you rule. One round per gap; each must be one specific question with a fact-shaped answer, not a topic. Empty when nothing here is a missing fact.',
    },
  },
}

const FOLDED = {
  type: 'object',
  additionalProperties: false,
  required: ['slug', 'answered', 'questionsDeleted', 'headline'],
  properties: {
    slug: { type: 'string', description: 'the front matter slug, unchanged by the fold' },
    answered: { type: 'array', items: { type: 'string' }, description: 'one line per question: what the human decided, and where in spec.md it now lives' },
    questionsDeleted: { type: 'boolean', description: 'true only if you actually deleted questions.md. Its absence is what makes the spec approvable (\u00a711).' },
    headline: { type: 'string', description: 'terse \u2014 what the answers changed' },
  },
}

const RESEARCH_ROUNDS_PER_GAP = (args && args.researchRoundsPerGap) || 1

function noRuling(afterPass) {
  return {
    verdict: 'block',
    settled: [], assumed: [], research: [], chosen: [],
    questions: ['The unblocker returned no ruling after the ' + afterPass + ' pass.'],
    why: 'agent failure \u2014 nothing ruled on the open questions, so nothing may be assumed past',
  }
}

// The shape of anything the human is asked, in EVERY gap. This used to live only in the
// last gap's instructions, so a run that blocked at the draft gap emitted a wall of dense
// prose -- the exact failure section 11 exists to prevent, surviving in the one path
// nobody had exercised.
const QUESTION_SHAPE = [
  '`questions` is whatever the human is asked, and it is the FIRST thing they read -- before the',
  'spec, if there is one. Section 11 binds its shape whichever gap emits it:',
  '  - at most THREE. Past three, say for each extra one why the ladder failed for it.',
  '  - at most 40 lines each, and a title that reads as a question.',
  '  - each carries its fork as NAMED OPTIONS, what changes down each branch, and the cost of',
  '    being wrong. Draw the fork as a plain-text diagram where that beats a paragraph.',
  '  - a recommendation ONLY where a voice won the argument, reported as that -- which voice and on',
  '    what grounds. Where they were tied, offer none and SAY SO: the absence tells the human the',
  '    decision is theirs alone.',
  '  - ordinary technical English. Do not use a term this run invented unless you define it there.',
  'An empty `questions` is the best outcome available. Do not manufacture one.',
].join('\n')

// In the last gap the unblocker does a second job: it rules on every point the rebut
// pass left disputed, so synthesis never receives one (section 5, section 10).
const SEAM_DUTY = [
  'This is the LAST gap, so you have a second job.',
  'Read every rebuttal in ' + WORK + '/. Every point a voice marked DISPUTED is a question too:',
  'two voices argued and neither won. Rule on each by what being wrong costs.',
  '  fatal-if-wrong  -> it goes in `questions`, for the human',
  '  anything else   -> you settle it. Put it in `chosen`: take the side that won the argument,',
  '                     or where neither did, pick one and say that is what you did.',
  'A contested cut is a disputed point: the agile agent vetoed a requirement, another voice tied it',
  'to the brief and lost anyway. It runs through this same filter (section 10).',
].join('\n')

function unblocker(afterPass, round, note) {
  return agent(
    [
      LAW,
      '',
      'You are running the gap after the ' + afterPass + ' pass.',
      'Sweep every open question raised so far in ' + WORK + '/, then rule on what survives.',
      note,
      'Append to the assumption register at ' + WORK + '/assumptions.md. Never rewrite it.',
      'Each entry says which it is: CHOSEN where you ruled, ASSUMED where nobody knew. Do not write',
      'assumed over a ruling, and do not write chosen over a coin-toss (section 5).',
      'Blocking is exceptional: if you block, name why no assumption was safe.',
      'A question another voice marked fatal-if-wrong you may not assume past. You may only record',
      'that you disagreed. The cap of three questions in section 11 does not overrule that mark',
      'either: it costs you an explanation, not the mark.',
      afterPass === 'Rebut' ? SEAM_DUTY : '',
      QUESTION_SHAPE,
    ].join('\n'),
    {
      agentType: 'unblocker',
      schema: RULING,
      label: 'unblocker:' + afterPass.toLowerCase() + (round ? '-r' + round : ''),
      phase: afterPass,
    }
  )
}

// The unblocker runs in every gap between passes (section 10) and owns rung 1 of the
// question ladder by delegation (section 5). It cannot spawn the researcher itself --
// no spec role can -- so the delegation happens HERE: it names the questions,
// the workflow fires the researcher on them, and it rules again with the
// answers. Left to itself the unblocker just reasons about whether research
// would have helped, which is not the same thing as researching.
async function gap(afterPass) {
  let ruling = await unblocker(
    afterPass,
    0,
    'Rung 1 is yours by delegation. Name in `research` every question that is a missing FACT rather\n' +
    'than a decision; the workflow sends them to the researcher and asks you again with the answers.\n' +
    'You get ' + RESEARCH_ROUNDS_PER_GAP + ' round in this gap. Naming nothing forfeits it.'
  )
  if (!ruling) return noRuling(afterPass)

  for (let round = 1; round <= RESEARCH_ROUNDS_PER_GAP; round += 1) {
    const questions = ruling.research || []
    if (!questions.length) break

    log('gap after ' + afterPass + ': researching ' + questions.length + ' named question(s)')
    await parallel(questions.map((q, n) => () =>
      agent(
        [
          LAW,
          '',
          'The unblocker has named this question in the gap after the ' + afterPass + ' pass:',
          '',
          q,
          '',
          'Answer that question and nothing around it. Repo first, then local documentation, then the',
          'web \u2014 never reach outside before the inside has failed. Cite every finding, preferring',
          'primary sources.',
          'If it has no fact-shaped answer \u2014 if it is a decision rather than a missing fact \u2014 say so',
          'plainly and stop. That is a useful answer.',
          // One file per researcher, never a shared one. These run in parallel, and an
          // append to a file three siblings are also appending to is a race: on the first
          // real run of this chain, four researchers reported success into one file and
          // three findings were lost, silently, leaving the unblocker to rule on a quarter
          // of the evidence it had commissioned.
          'Write your finding to ' + WORK + '/research-' + afterPass.toLowerCase() + '-' + (n + 1) + '.md,',
          'under a heading quoting the question. That file is yours alone: create it, do not append',
          'to any other file, and do not touch a sibling2019s.',
        ].join('\n'),
        { agentType: 'researcher', label: 'research:' + afterPass.toLowerCase() + '-' + (n + 1), phase: afterPass }
      )
    ))

    const reruled = await unblocker(
      afterPass,
      round,
      'The researchers have answered the questions you named, one file each. Read ALL of\n' +
      WORK + '/research-' + afterPass.toLowerCase() + '-*.md before you rule 2014 there is one per\n' +
      'question you named, numbered in the order you named them. A file that is missing is a failed\n' +
      'agent, not a question you may treat as unresearched: say which number is absent.\n' +
      'Fold every answered question into `settled` and rule on what is left. Your research rounds for\n' +
      'this gap are now spent, so leave `research` empty.'
    )
    if (!reruled) return noRuling(afterPass)
    ruling = reruled
  }

  log('gap after ' + afterPass + ': ' + ruling.verdict + ' \u2014 ' + ruling.settled.length + ' settled, ' +
      ruling.assumed.length + ' assumed, ' + (ruling.chosen || []).length + ' chosen, ' +
      (ruling.questions || []).length + ' for the human')
  return ruling
}

function blocked(ruling, at) {
  return {
    outcome: 'blocked',
    at: at,
    questions: ruling.questions,
    why: ruling.why,
    next: 'Answer the batch in ' + RUN + '/answers.md, then run /spec-swarm again.',
  }
}

function askHumanToRead(reason) {
  return { outcome: 'unknown', reason: reason, artifact: RUN }
}

function spend() {
  if (!budget.total) return 'no ceiling set'
  return Math.round(budget.remaining() / 1000) + 'k of ' + Math.round(budget.total / 1000) + 'k left'
}

// The token budget is the only ceiling this harness has, and it is a hard one: agent()
// throws once it is spent. Dying inside a pass would leave the human an exception and a
// half-written blackboard, so we stop ourselves one pass short instead -- exhaustion is a
// halt, not a crash (section 12). A pass is every voice at once, so the floor is a whole
// pass's worth. It is a floor, not a guarantee: a pass can still overrun it.
const FLOOR = 60000

function outOfBudget() {
  return Boolean(budget.total) && budget.remaining() < FLOOR
}

// The blackboard survives, so the next run picks up where this one stopped: a run that
// reached the drafts resumes at critique exactly as a blocked one does.
function exhausted(at) {
  return {
    outcome: 'budget-exhausted',
    at: at,
    budget: spend(),
    artifact: RUN,
    next: 'The blackboard in ' + WORK + ' is intact. Raise the token budget and run /spec-swarm again.',
  }
}

// ---------------------------------------------------------------------------
// Fold. The run already reached the seam and the human has answered the
// questions it could not settle, so nothing needs re-arguing: only the spec
// writer runs (section 10). Re-running the voices here would change text the
// human had already read and accepted.
// ---------------------------------------------------------------------------

if (mode === 'fold') {
  phase('Synthesis')
  log('folding the answers in ' + RUN + '/answers.md into the spec. Spec writer only. Budget: ' + spend())

  if (outOfBudget()) return exhausted('fold')

  const folded = await agent(
    [
      LAW,
      '',
      'This is a FOLD (section 10). The spec at ' + RUN + '/spec.md went to the human, who has',
      'answered the questions it could not settle. You are the only agent running.',
      'Read ' + RUN + '/questions.md and ' + RUN + '/answers.md.',
      'Write each answer into ' + RUN + '/spec.md where it belongs -- into the requirement, the',
      'register, or the out-of-scope list, as the answer dictates. The human wrote prose; you keep',
      'the structure. Their answers outrank anything in the spec that contradicts them.',
      'Do not re-open the debate, do not add requirements no voice raised, and do not touch',
      'brief.md or the front matter. Only a human writes status: approved (section 11).',
      'Then DELETE ' + RUN + '/questions.md. Its absence is what says nothing is left to answer,',
      'and it is the only mechanical check the disposition rule has (section 11).',
      'Never leave the same decision written in two files.',
    ].join('\n'),
    { agentType: 'spec-writer', schema: FOLDED, label: 'spec-writer:fold', phase: 'Synthesis' }
  )

  if (!folded) return askHumanToRead('the spec writer returned nothing from the fold \u2014 read the run directory before trusting it')
  if (!folded.questionsDeleted) {
    return askHumanToRead('the fold did not delete ' + RUN + '/questions.md, so the seam is still open and the spec is not approvable')
  }

  return {
    outcome: 'folded',
    artifact: RUN,
    slug: folded.slug,
    folded: folded.answered,
    headline: folded.headline,
    next: 'Read ' + RUN + '/spec.md and set status: approved yourself. Nothing is left to answer.',
  }
}

// ---------------------------------------------------------------------------
// Sweep and draft. Skipped on a resume: the drafts already exist on the
// blackboard and re-entry is at critique (section 10).
// ---------------------------------------------------------------------------

if (mode === 'resume') {
  log(hasAnswers
    ? 'resuming with the answers in ' + RUN + '/answers.md \u2014 re-entering at critique over the existing drafts'
    : 'resuming a run that stopped for budget \u2014 re-entering at critique over the existing drafts')
} else {
  phase('Sweep')
  log('fresh run. Voices: ' + voices.join(', ') + '. Budget: ' + spend())

  if (outOfBudget()) return exhausted('sweep')

  await agent(
    [
      LAW,
      '',
      'This is the opening sweep. Read the brief and pull out every question the voices would',
      'otherwise each go fetching for themselves: facts about this repo, the platform, the tools',
      'the brief names, and any third party it implies. Repo first, then local docs, then the web.',
      'Write your findings to ' + WORK + '/research-sweep.md, each one citing its source.',
    ].join('\n'),
    { agentType: 'researcher', label: 'sweep', phase: 'Sweep' }
  )

  const afterSweep = await gap('Sweep')
  if (afterSweep.verdict === 'block') return blocked(afterSweep, 'sweep')

 // Draft is independent (section 10) -- no voice sees another's draft. This barrier is
 // real: critique cannot start until every draft exists.
  phase('Draft')
  if (outOfBudget()) return exhausted('draft')

  await parallel(voices.map((v) => () =>
    agent(
      [
        LAW,
        '',
        'Draft pass. Read ' + WORK + '/research-sweep.md and the brief. Do NOT read another voice\u2019s',
        'draft \u2014 they do not exist yet, and divergence is the point.',
        'Draft what you think should be built, from your own remit only.',
        'Write it to ' + WORK + '/draft-' + v + '.md, ending with a section titled "Open questions".',
      ].join('\n'),
      { agentType: v, label: 'draft:' + v, phase: 'Draft' }
    )
  ))

  const afterDraft = await gap('Draft')
  if (afterDraft.verdict === 'block') return blocked(afterDraft, 'draft')
}

// ---------------------------------------------------------------------------
// Critique, rebut, synthesis. A resume re-enters here (section 10).
// ---------------------------------------------------------------------------

const answersNote = hasAnswers
  ? '\nThe human has answered the last run\u2019s blocking questions in ' + RUN + '/answers.md. Read it first.\n' +
    'Those answers outrank anything in the drafts that contradicts them.'
  : ''

phase('Critique')
if (outOfBudget()) return exhausted('critique')

await parallel(voices.map((v) => () =>
  agent(
    [
      LAW,
      answersNote,
      '',
      'Critique pass \u2014 the first pass where you read everyone. Read every ' + WORK + '/draft-*.md,',
      'including your own, and ' + WORK + '/assumptions.md.',
      'Critique each draft that is not yours, from your remit. Be specific: a critique that does not',
      'name the requirement it attacks is noise.',
      'Write to ' + WORK + '/critique-' + v + '.md, one section per draft you attacked.',
    ].join('\n'),
    { agentType: v, label: 'critique:' + v, phase: 'Critique' }
  )
))

const afterCritique = await gap('Critique')
if (afterCritique.verdict === 'block') return blocked(afterCritique, 'critique')

phase('Rebut')
if (outOfBudget()) return exhausted('rebut')

await parallel(voices.map((v) => () =>
  agent(
    [
      LAW,
      answersNote,
      '',
      'Rebut pass. Read every ' + WORK + '/critique-*.md and answer only the critiques aimed at your',
      'own draft, ' + WORK + '/draft-' + v + '.md.',
      'Mark each critique agreed, conceded, or disputed. Only disputed points reach synthesis',
      'unresolved, so do not dispute what you merely dislike.',
      'Write to ' + WORK + '/rebut-' + v + '.md.',
    ].join('\n'),
    // Answering critiques of a draft that already exists is lighter than writing it, and
    // lighter than attacking three others. Section 12 lets the orchestrator lower a role's
    // declared effort for a lighter pass, never raise it.
    { agentType: v, label: 'rebut:' + v, phase: 'Rebut', effort: 'medium' }
  )
))

const afterRebut = await gap('Rebut')
if (afterRebut.verdict === 'block') return blocked(afterRebut, 'rebut')

phase('Synthesis')
log('synthesising. Budget: ' + spend())

if (outOfBudget()) return exhausted('synthesis')

// The open questions are no longer the spec writer's. The unblocker ruled on every
// disputed point in the last gap, so what reaches the human is `afterRebut.questions`
// and it lives in its own file, not in a section of spec.md (section 11). The spec
// writer's job here is the artifact and nothing else.
const WRITTEN = {
  type: 'object',
  additionalProperties: false,
  required: ['slug', 'degraded', 'headline'],
  properties: {
    slug: { type: 'string', description: 'the front matter slug \u2014 the branch name and the task name' },
    degraded: { type: 'array', items: { type: 'string' }, description: 'gate steps declared missing (\u00a72)' },
    headline: { type: 'string', description: 'terse \u2014 what the spec asks for' },
  },
}

const written = await agent(
  [
    LAW,
    answersNote,
    '',
    'Synthesis. You are the last agent before the human. Merge \u2014 do not adjudicate.',
    'Read everything in ' + WORK + '/: the drafts, the critiques, the rebuttals, the assumption',
    'register, and the research. Then write the artifact, from swarm/templates/:',
    '  ' + RUN + '/spec.md             the fixed order below',
    '  ' + RUN + '/acceptance.feature  the acceptance criteria, in Gherkin',
    'Leave brief.md exactly as it is.',
    'The order of spec.md is fixed (\u00a711): the degraded-gate warning if this run is degraded, then',
    'the requirements, then the assumption register, then out of scope, then research links. The',
    'warning is first because it changes what approval means. The requirements are next because the',
    'main reader of this file is the architect.',
    'Front matter is status: draft and revision: 1. Only a human writes approved (\u00a711).',
    'You write NO open-questions section. Every disputed point was ruled on by the unblocker in the',
    'last gap: what it chose is settled text with a register entry, and what it could not settle is',
    'the human\u2019s batch, which lives in its own file and is not yours. If a dispute reaches you',
    'unruled, say so in your headline rather than deciding it.',
    'Each register entry says CHOSEN or ASSUMED, as the unblocker recorded it. Do not flatten them.',
    'Ordinary technical English (\u00a711). Define any term this run invented, at first use, or drop it.',
    'Where an idea is a chain, a fork or a set of states, draw it as a plain-text diagram rather than',
    'describing it in a paragraph. Plain text, not mermaid: this file is read in an editor.',
    'Read .swarm/gate.yaml. If any step is missing, say so plainly at the very top of spec.md \u2014 this',
    'will be a degraded run, and the human approves knowing what will not be checked (\u00a72).',
  ].join('\n'),
  { agentType: 'spec-writer', schema: WRITTEN, label: 'spec-writer', phase: 'Synthesis' }
)

if (!written) return askHumanToRead('the spec writer returned nothing \u2014 read the run directory before trusting it')
if (written.degraded.length) log('degraded run \u2014 the gate has no tool for: ' + written.degraded.join(', '))

// The questions are the unblocker's, not the spec writer's, and they go in their own
// file. The skill writes them, verbatim -- this script cannot touch the filesystem.
const seamQuestions = afterRebut.questions || []

return {
  outcome: 'drafted',
  artifact: RUN,
  slug: written.slug,
  assumptions: afterRebut.assumed,
  chosen: afterRebut.chosen || [],
  questions: seamQuestions,
  degraded: written.degraded,
  headline: written.headline,
  next: seamQuestions.length
    ? 'Write these ' + seamQuestions.length + ' question(s) to ' + RUN + '/questions.md verbatim. ' +
      'The human answers them in ' + RUN + '/answers.md, in prose, then runs /spec-swarm again for a fold.'
    : 'Nothing is left to answer. Read ' + RUN + '/spec.md and set status: approved yourself.',
}
