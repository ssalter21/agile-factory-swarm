export const meta = {
  name: 'build-chain',
  description: 'Turn the approved spec into a merged change (constitution §6, §11)',
  whenToUse: 'Runs the builder chain of §6. Invoked only by the /build-swarm skill, which checks approval first.',
  phases: [
    { title: 'Plan', detail: 'architect restates the spec, diffs it, then plans' },
    { title: 'Build', detail: 'coder, cleaner, hardener — appeals and bounces resolve here' },
    { title: 'Conformance', detail: 'architect checks the built code against its own plan' },
    { title: 'QA', detail: 'acceptance through the interface only, then the pull request' },
  ],
}

// ---------------------------------------------------------------------------
// There is no resume path here, and that is deliberate: §11 says an amended spec
// restarts at the architect, and the chain already starts at the architect. The
// restart is simply invoking this workflow again on the same branch.
// ---------------------------------------------------------------------------

const RUN = '.swarm/runs/current'
const PLAN = '.scratch/plan.md'
const CHAIN = ['coder', 'cleaner', 'hardener']
const MAX_APPEALS = 3

const LAW = [
  'You are bound by swarm/constitution.md. Read it before you act: §6 is the handoff contract,',
  '§2 is the quality gate, §11 is the seam.',
  'The approved spec is at ' + RUN + '/spec.md and its acceptance criteria at ' + RUN + '/acceptance.feature.',
  'It is the only authority on what to build. The plan at ' + PLAN + ' is the law on where the code goes.',
  'Run gate commands in the shell .swarm/gate.yaml declares. Never substitute another shell.',
  'Report a missing step as missing. It is a debt, not a pass, and the run is degraded (§2).',
].join('\n')

const HANDOFF = {
  type: 'object',
  additionalProperties: false,
  required: ['task', 'changed', 'gate', 'deviations', 'request', 'status', 'summary'],
  properties: {
    task: { type: 'string', description: 'the stable task name, preserved across every hop (§6)' },
    changed: { type: 'array', items: { type: 'string' }, description: 'files this role touched' },
    gate: {
      type: 'array',
      description: 'every gate step you ran: your own and every step owned by a role before you',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['step', 'result'],
        properties: {
          step: { type: 'string', enum: ['tests', 'coverage', 'duplication', 'mutation', 'crap', 'acceptance'] },
          result: { type: 'string', enum: ['pass', 'fail', 'missing'] },
        },
      },
    },
    deviations: { type: 'array', items: { type: 'string' }, description: 'appeals made, and how the architect ruled' },
    request: { type: 'string', description: 'what the next role is being asked for' },
    status: {
      type: 'string',
      enum: ['forward', 'appeal', 'bounce', 'halt'],
      description: 'forward: hand on, including when nothing changed. appeal: the plan blocks correct work. bounce: the problem belongs to an earlier role. halt: the approved spec is wrong.',
    },
    summary: { type: 'string', description: 'terse. State, not narration (§6).' },
    bounceTo: {
      type: 'string',
      enum: ['coder', 'cleaner', 'hardener'],
      description: 'required with status bounce: the earlier role the problem belongs to, which §6 sends it back to once, with the reproduction.',
    },
  },
}

function spend() {
  if (!budget.total) return 'no ceiling set'
  return Math.round(budget.remaining() / 1000) + 'k of ' + Math.round(budget.total / 1000) + 'k left'
}

function halted(h, at) {
  return {
    outcome: 'halted',
    at: at,
    contradiction: h ? h.summary : 'the ' + at + ' returned nothing',
    next: 'Amend ' + RUN + '/spec.md, bump revision, and run /build-swarm again. It restarts at the architect (§11).',
  }
}

function askHuman(reason, at, h) {
  return {
    outcome: 'human-question',
    at: at,
    reason: reason,
    detail: h ? h.summary : '',
    next: 'Settle it, then run /build-swarm again on this branch.',
  }
}

// ---------------------------------------------------------------------------
// Plan. Restate and diff is the architect's first action, before it plans (§11).
// ---------------------------------------------------------------------------

phase('Plan')
log('build swarm. Budget: ' + spend())

let plan = await agent(
  [
    LAW,
    '',
    'First pass. Before you plan anything: restate the approved spec in your own words to',
    '.scratch/restatement.md, then diff your restatement against the spec (§11).',
    'A contradiction, or a requirement you cannot account for, halts the run — return status halt',
    'and name the gap. No other role may settle it.',
    'An ambiguity you can resolve defensibly is a named interpretation, recorded in the restatement.',
    'It travels in the handoff and QA checks it at the end.',
    'Then write the plan to ' + PLAN + ': module boundaries, dependency direction, the testability',
    'boundary (§3), and what is forbidden. It is a handover, not an artifact — never commit it.',
    'You own no gate step. Run none.',
  ].join('\n'),
  { agentType: 'architect', schema: HANDOFF, label: 'architect:plan', phase: 'Plan' }
)

if (!plan || plan.status === 'halt') return halted(plan, 'architect (plan)')

const task = plan.task
let deviations = plan.deviations.slice()

// ---------------------------------------------------------------------------
// Build, conformance and QA. Sequential by construction — each role hands to
// the next, and appeals and bounces are resolved here rather than by the roles
// talking to each other.
//
// A bounce from a reviewing role re-enters the build chain at the role that owns
// the problem, and everything downstream of it runs again. §6 gives one bounce
// per role; a second failure of the same thing is a human question.
// ---------------------------------------------------------------------------

let appeals = 0
const bounced = {}
let last = plan
let entry = 0

// One trip through the build chain, starting at `entry`. Returns a terminal
// result for the workflow to return, or null when the chain reached the end.
async function runChain() {
  let i = entry
  while (i < CHAIN.length) {
    const role = CHAIN[i]
    const h = await agent(
      [
        LAW,
        '',
        'Task: ' + task,
        'The plan is at ' + PLAN + '. Read it, and read .scratch/restatement.md for the architect’s',
        'named interpretations.',
        'Upstream asked for: ' + last.request,
        'Upstream state: ' + last.summary,
        '',
        'Run every gate step you own and every step owned by a role before you in the chain, in',
        'constitutional order (§2). Never hand on work that fails your own step — fix it or escalate.',
        'Return status forward even when you changed nothing. A chain that silently stops is worse',
        'than one that passes an empty result.',
        'Use appeal only when the plan blocks correct work, and bounce only when the problem is real',
        'and belongs to an earlier role. Fix inside your own remit before bouncing, and name that',
        'role in bounceTo.',
      ].join('\n'),
      { agentType: role, schema: HANDOFF, label: role, phase: 'Build' }
    )

    if (!h) return askHuman('the ' + role + ' returned nothing', role, null)
    if (h.status === 'halt') return halted(h, role)

    if (h.status === 'appeal') {
      appeals += 1
      log('appeal ' + appeals + ' of ' + MAX_APPEALS + ' from the ' + role)
      if (appeals > MAX_APPEALS) return askHuman('a fourth appeal on this task (§6)', role, h)

      const ruling = await agent(
        [
          LAW,
          '',
          'Task: ' + task,
          'The ' + role + ' has appealed: your plan blocks correct work.',
          'Their case: ' + h.summary,
          'Rule on it. If they are right, amend ' + PLAN + ' and say what changed. If they are wrong,',
          'say why and leave the plan as it is. Either way the ' + role + ' resumes after you.',
        ].join('\n'),
        { agentType: 'architect', schema: HANDOFF, label: 'architect:appeal-' + appeals, phase: 'Build' }
      )
      if (!ruling || ruling.status === 'halt') return halted(ruling, 'architect (appeal)')
      deviations = deviations.concat(['appeal from ' + role + ': ' + ruling.summary])
      last = ruling
      continue // same role, amended plan
    }

    if (h.status === 'bounce') {
      if (i === 0) return askHuman('the coder bounced with nothing upstream of it to bounce to', role, h)
      if (bounced[role]) return askHuman('the ' + role + ' bounced the same thing twice (§6)', role, h)
      bounced[role] = true
      log('bounce from the ' + role + ' back to the ' + CHAIN[i - 1])
      last = h
      i -= 1
      continue
    }

    deviations = deviations.concat(h.deviations)
    last = h
    i += 1
  }
  return null
}

// A bounce from a reviewing role — the architect's conformance pass, or QA —
// re-enters the chain at the role that owns the problem. Everything downstream
// of it runs again, because a role that ran before the fix has not seen it.
function reenter(h, from) {
  const target = h.bounceTo
  if (CHAIN.indexOf(target) < 0) {
    return askHuman('the ' + from + ' bounced without naming a role in the chain to bounce to', from, h)
  }
  if (bounced[target]) {
    return askHuman('the ' + target + ' has already been bounced once on this task (§6)', from, h)
  }
  bounced[target] = true
  entry = CHAIN.indexOf(target)
  last = h
  deviations = deviations.concat(['bounce from ' + from + ' to ' + target + ': ' + h.summary])
  log('bounce from the ' + from + ' back to the ' + target + ' — the chain re-runs from there')
  return null
}

let qa = null

while (true) {
  phase('Build')
  const chainStopped = await runChain()
  if (chainStopped) return chainStopped

  // -------------------------------------------------------------------------
  // Conformance. The architect's second pass — it checks the code against the
  // plan it wrote, and it still edits nothing.
  // -------------------------------------------------------------------------

  phase('Conformance')

  const conformance = await agent(
    [
      LAW,
      '',
      'Task: ' + task,
      'Second pass. The chain is built. Check the code against the plan at ' + PLAN + ' and against',
      'the interpretations in .scratch/restatement.md.',
      'You are read-only. You do not fix what you find — you rule on it.',
      'Deviations so far: ' + (deviations.length ? deviations.join('; ') : 'none'),
      'Hand to QA when the code conforms. When it does not, bounce and name the role that owns the',
      'fix in bounceTo; that role and everything after it runs again.',
      'Correcting your own plan is an amendment, not a bounce, and costs the appealing role nothing.',
    ].join('\n'),
    { agentType: 'architect', schema: HANDOFF, label: 'architect:conformance', phase: 'Conformance' }
  )

  if (!conformance) return askHuman('the architect returned nothing on its conformance pass', 'architect (conformance)', null)
  if (conformance.status === 'halt') return halted(conformance, 'architect (conformance)')
  if (conformance.status === 'bounce') {
    const stop = reenter(conformance, 'architect (conformance)')
    if (stop) return stop
    continue
  }

  // -------------------------------------------------------------------------
  // QA. Terminal. Runs all six gate steps and assembles the durable record.
  // -------------------------------------------------------------------------

  phase('QA')
  log('QA. Budget: ' + spend())

  qa = await agent(
    [
      LAW,
      '',
      'Task: ' + task,
      'You are the last role. Nothing downstream catches what you miss.',
      'Exercise this through its user interface only (§9). Never call an API into the project to',
      'make a test pass.',
      'Validate against ' + RUN + '/acceptance.feature, not against the code. Where they disagree,',
      'the criteria win: code that fails a criterion is a defect, so bounce with the reproduction and',
      'name the coder in bounceTo; a criterion that cannot be satisfied, or two that contradict each',
      'other, is the spec being wrong, so halt.',
      'Check every named interpretation in .scratch/restatement.md.',
      'Run all six gate steps (§2). Name every missing one — this run is degraded and the report says so.',
      'The criteria survive only as something that runs (§11): commit the feature file into the test',
      'tree where a runner exists, otherwise write ordinary tests against the same criteria and let',
      'the feature file die with the run directory. Never commit a feature file nothing executes.',
      'Then assemble the durable record: open the pull request, its body built from the brief, the',
      'spec, the assumption register, and the out-of-scope list, so the reviewer reads the contract',
      'beside the diff. Where the repo has no pull request mechanism, emit the same text here.',
      'Deviations across the run: ' + (deviations.length ? deviations.join('; ') : 'none'),
    ].join('\n'),
    { agentType: 'qa', schema: HANDOFF, label: 'qa', phase: 'QA' }
  )

  if (!qa) return askHuman('QA returned nothing', 'qa', null)
  if (qa.status === 'halt') return halted(qa, 'qa')
  if (qa.status === 'bounce') {
    const stop = reenter(qa, 'qa')
    if (stop) return stop
    continue
  }

  break
}

const degraded = qa.gate.filter((g) => g.result === 'missing').map((g) => g.step)
if (degraded.length) log('degraded run — no tool for: ' + degraded.join(', '))

return {
  outcome: 'built',
  task: task,
  gate: qa.gate,
  degraded: degraded,
  deviations: deviations,
  summary: qa.summary,
}
