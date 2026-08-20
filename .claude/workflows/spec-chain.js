export const meta = {
  name: 'spec-chain',
  description: 'Turn the brief in the run directory into an approvable spec (constitution §10)',
  whenToUse: 'Runs the five passes of §10. Invoked only by the /spec-swarm skill, which owns the blackboard writes and the seam.',
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
const WORK = RUN + '/work'

const mode = (args && args.mode) || 'fresh'
const voices = (args && args.voices) || ['agile-agent', 'user-voice', 'domain-modeller', 'devils-advocate']

const LAW = [
  'You are bound by swarm/constitution.md. Read it before you act: §10 places you in the spec swarm,',
  '§5 is the question ladder, §11 is the seam.',
  'Read ' + RUN + '/brief.md and .swarm/spec.yaml first. The brief is what was asked for; spec.yaml',
  'says who the user is and what the domain is.',
  'Write your output to the file named below, and return ONLY a terse pointer to it plus your',
  'headline. Never return the file contents. Your return value is machinery, not a message.',
].join('\n')

const RULING = {
  type: 'object',
  additionalProperties: false,
  required: ['verdict', 'settled', 'assumed', 'blocking', 'why'],
  properties: {
    verdict: {
      type: 'string',
      enum: ['continue', 'block', 'restart'],
      description: 'continue: assumptions cover the gaps. block: a question no assumption is safe for. restart: a human answer broke a premise, so drafting must happen again.',
    },
    settled: { type: 'array', items: { type: 'string' }, description: 'questions research answered' },
    assumed: { type: 'array', items: { type: 'string' }, description: 'each assumption, then its cost if wrong' },
    blocking: { type: 'array', items: { type: 'string' }, description: 'questions for the human; empty unless verdict is block' },
    why: { type: 'string', description: 'if blocking, why no assumption was safe. §5 requires this.' },
    research: {
      type: 'array',
      items: { type: 'string' },
      description: 'named questions to send to the researcher before you rule. One round per gap; each must be one specific question with a fact-shaped answer, not a topic. Empty when nothing here is a missing fact.',
    },
  },
}

const RESEARCH_ROUNDS_PER_GAP = (args && args.researchRoundsPerGap) || 1

function noRuling(afterPass) {
  return {
    verdict: 'block',
    settled: [], assumed: [], research: [],
    blocking: ['The unblocker returned no ruling after the ' + afterPass + ' pass.'],
    why: 'agent failure — nothing ruled on the open questions, so nothing may be assumed past',
  }
}

function unblocker(afterPass, round, note) {
  return agent(
    [
      LAW,
      '',
      'You are running the gap after the ' + afterPass + ' pass.',
      'Sweep every open question raised so far in ' + WORK + '/, then rule on what survives.',
      note,
      'Append to the assumption register at ' + WORK + '/assumptions.md. Never rewrite it.',
      'Blocking is exceptional: if you block, name why no assumption was safe.',
      'A question another voice marked fatal-if-wrong you may not assume past. You may only record',
      'that you disagreed.',
    ].join('\n'),
    {
      agentType: 'unblocker',
      schema: RULING,
      label: 'unblocker:' + afterPass.toLowerCase() + (round ? '-r' + round : ''),
      phase: afterPass,
    }
  )
}

// The unblocker runs in every gap between passes (§10) and owns rung 1 of the
// question ladder by delegation (§5). It cannot spawn the researcher itself —
// no spec role can — so the delegation happens HERE: it names the questions,
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
          'web — never reach outside before the inside has failed. Cite every finding, preferring',
          'primary sources.',
          'If it has no fact-shaped answer — if it is a decision rather than a missing fact — say so',
          'plainly and stop. That is a useful answer.',
          'Append your finding to ' + WORK + '/research-' + afterPass.toLowerCase() + '.md under a',
          'heading quoting the question.',
        ].join('\n'),
        { agentType: 'researcher', label: 'research:' + afterPass.toLowerCase() + '-' + (n + 1), phase: afterPass }
      )
    ))

    const reruled = await unblocker(
      afterPass,
      round,
      'The researcher has answered the questions you named. Read\n' +
      WORK + '/research-' + afterPass.toLowerCase() + '.md before you rule.\n' +
      'Fold every answered question into `settled` and rule on what is left. Your research rounds for\n' +
      'this gap are now spent, so leave `research` empty.'
    )
    if (!reruled) return noRuling(afterPass)
    ruling = reruled
  }

  log('gap after ' + afterPass + ': ' + ruling.verdict + ' — ' + ruling.settled.length + ' settled, ' +
      ruling.assumed.length + ' assumed, ' + ruling.blocking.length + ' blocking')
  return ruling
}

function blocked(ruling, at) {
  return {
    outcome: 'blocked',
    at: at,
    questions: ruling.blocking,
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

// ---------------------------------------------------------------------------
// Sweep and draft. Skipped on a resume: the drafts already exist on the
// blackboard and re-entry is at critique (§10).
// ---------------------------------------------------------------------------

if (mode === 'resume') {
  log('resuming with the answers in ' + RUN + '/answers.md — re-entering at critique over the existing drafts')
} else {
  phase('Sweep')
  log('fresh run. Voices: ' + voices.join(', ') + '. Budget: ' + spend())

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

  // Draft is independent (§10) — no voice sees another's draft. This barrier is
  // real: critique cannot start until every draft exists.
  phase('Draft')
  await parallel(voices.map((v) => () =>
    agent(
      [
        LAW,
        '',
        'Draft pass. Read ' + WORK + '/research-sweep.md and the brief. Do NOT read another voice’s',
        'draft — they do not exist yet, and divergence is the point.',
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
// Critique, rebut, synthesis. A resume re-enters here (§10).
// ---------------------------------------------------------------------------

const answersNote = mode === 'resume'
  ? '\nThe human has answered the last run’s blocking questions in ' + RUN + '/answers.md. Read it first.\n' +
    'Those answers outrank anything in the drafts that contradicts them.'
  : ''

phase('Critique')
await parallel(voices.map((v) => () =>
  agent(
    [
      LAW,
      answersNote,
      '',
      'Critique pass — the first pass where you read everyone. Read every ' + WORK + '/draft-*.md,',
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
    { agentType: v, label: 'rebut:' + v, phase: 'Rebut' }
  )
))

const afterRebut = await gap('Rebut')
if (afterRebut.verdict === 'block') return blocked(afterRebut, 'rebut')

phase('Synthesis')
log('synthesising. Budget: ' + spend())

// The spec's open questions are the points still disputed after the rebut pass.
// They are NOT the unblocker's blocking list — that is empty whenever the run
// reaches synthesis at all, so reading it here reports zero open questions on
// every spec that was ever written.
const WRITTEN = {
  type: 'object',
  additionalProperties: false,
  required: ['slug', 'openQuestions', 'degraded', 'headline'],
  properties: {
    slug: { type: 'string', description: 'the front matter slug — the branch name and the task name' },
    openQuestions: { type: 'array', items: { type: 'string' }, description: 'one line per disputed point shipped for the human to disposition' },
    degraded: { type: 'array', items: { type: 'string' }, description: 'gate steps declared missing (§2)' },
    headline: { type: 'string', description: 'terse — what the spec asks for' },
  },
}

const written = await agent(
  [
    LAW,
    answersNote,
    '',
    'Synthesis. You are the last agent before the human. Merge — do not adjudicate.',
    'Read everything in ' + WORK + '/: the drafts, the critiques, the rebuttals, the assumption',
    'register, and the research. Then write the artifact, from swarm/templates/:',
    '  ' + RUN + '/spec.md             front matter, assumption register, requirements, out of scope, open questions, research links',
    '  ' + RUN + '/acceptance.feature  the acceptance criteria, in Gherkin',
    'Leave brief.md exactly as it is.',
    'Front matter is status: draft and revision: 1. Only a human writes approved (§11).',
    'Every point still disputed after the rebut pass ships as an open question. You do not settle',
    'them; the human dispositions each one at the seam.',
    'Read .swarm/gate.yaml. If any step is missing, say so plainly near the top of spec.md — this',
    'will be a degraded run, and the human approves knowing what will not be checked (§2).',
  ].join('\n'),
  { agentType: 'spec-writer', schema: WRITTEN, label: 'spec-writer', phase: 'Synthesis' }
)

if (!written) return askHumanToRead('the spec writer returned nothing — read the run directory before trusting it')
if (written.degraded.length) log('degraded run — the gate has no tool for: ' + written.degraded.join(', '))

return {
  outcome: 'drafted',
  artifact: RUN,
  slug: written.slug,
  assumptions: afterRebut.assumed,
  openQuestions: written.openQuestions,
  degraded: written.degraded,
  headline: written.headline,
  next: 'Read ' + RUN + '/spec.md, disposition all ' + written.openQuestions.length +
        ' open questions, then set status: approved yourself.',
}
