import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { actionableHealthGroups, healthLabel, mediaValidationStatus } from '../src/lib/health.ts'
import type { ArtifactGroupSummary } from '../src/lib/types.ts'
import { aiPrevizCostBadge, hasRenderClipPrevizScope, previzPlaybackSummary } from '../src/components/previz-panel-support.ts'
import type { PrevizLaneStatus } from '../src/lib/previz-types.ts'

const fixture = JSON.parse(readFileSync(
  new URL('./fixtures/media-validation-needs-review.json', import.meta.url), 'utf8',
)) as { group: ArtifactGroupSummary }

test('a real locally checked cut awaiting semantic review is not called failed', () => {
  const { group } = fixture
  assert.equal(healthLabel(group.health, group.health_details), 'Needs Review')
  assert.equal(mediaValidationStatus(group.health, group.health_details)?.tone, 'pending')
  assert.equal(actionableHealthGroups([group]).length, 1)
})

test('validation labels distinguish review, failure, success, and obsolete reports', () => {
  const details = fixture.group.health_details
  for (const health of ['valid', 'healthy', 'confirmed_valid']) {
    assert.equal(healthLabel(health, details), 'Validated')
  }
  assert.equal(healthLabel('needs_revision', details), 'Validation Failed')
  assert.equal(mediaValidationStatus('needs_revision', details)?.tone, 'failed')
  for (const source_kind of ['media_validation_missing', 'media_validation_stale']) {
    assert.equal(healthLabel('needs_review', { ...details!, source_kind }), 'Validation Pending')
  }
  assert.equal(healthLabel('needs_review'), 'Needs Review')
})

test('AI previz never calls review-needed media ready in either clip layout', () => {
  for (const hasClipPrevizOutputs of [false, true]) {
    const summary = previzPlaybackSummary({
      sceneHeading: 'INT. TRAILER HOME - DAY',
      hasIncompleteCurrentClipSet: false,
      previzClipArtifactCount: 2,
      plannedClipCount: 2,
      hasClipPrevizOutputs,
      validationStatus: mediaValidationStatus(fixture.group.health, fixture.group.health_details),
    })
    assert.match(summary, /Review is still required/)
    assert.doesNotMatch(summary, /ready/)
  }
})

test('AI previz preserves pending, failed, ready, and incomplete guidance', () => {
  const base = {
    sceneHeading: 'INT. TRAILER HOME - DAY',
    hasIncompleteCurrentClipSet: false,
    previzClipArtifactCount: 1,
    plannedClipCount: 2,
    hasClipPrevizOutputs: true,
  }
  const details = fixture.group.health_details
  for (const [health, source_kind, expected] of [
    ['needs_review', 'media_validation_stale', /Validation is still pending/],
    ['needs_revision', 'media_validation', /validation flagged at least one/],
    ['valid', 'media_validation', /clips are ready/],
  ] as const) {
    assert.match(previzPlaybackSummary({
      ...base, validationStatus: mediaValidationStatus(health, { ...details!, source_kind }),
    }), expected)
  }
  assert.match(previzPlaybackSummary({
    ...base, hasIncompleteCurrentClipSet: true,
    validationStatus: mediaValidationStatus('valid', details),
  }), /1 of 2 render-clip players/)
})

test('current recipe cost badge labels one priced video example and never invents a blocked amount', () => {
  const example = {
    cost: {
      status: 'estimated',
      estimated_cost_usd: 0.2,
      duration_seconds: 4,
      basis: 'recipe_default_video_example',
      price: {
        provider: 'xai',
        model: 'grok-imagine-video',
        resolution: '480p',
        unit: 'USD/second',
        unit_price_usd: 0.05,
        source_url: 'https://docs.x.ai/',
        checked_on: '2026-10-23',
      },
    },
  } as unknown as PrevizLaneStatus
  assert.equal(aiPrevizCostBadge(example), '4s video example: $0.20 est.')
  assert.equal(
    aiPrevizCostBadge({ cost: { status: 'blocked', reason: 'Price unavailable' } } as PrevizLaneStatus),
    'Cost blocked',
  )
})

test('one planned or saved render clip uses the clip player and review controls', () => {
  assert.equal(hasRenderClipPrevizScope(1, true), true, 'a generated single clip must keep its player and actions')
  assert.equal(hasRenderClipPrevizScope(1, false), true, 'a missing single clip must expose its generation review action')
  assert.equal(hasRenderClipPrevizScope(0, true), true, 'saved clip outputs remain inspectable without a plan')
  assert.equal(hasRenderClipPrevizScope(2, true), true)
  assert.equal(hasRenderClipPrevizScope(0, false), false, 'scene-level output keeps the standalone viewer')
})
