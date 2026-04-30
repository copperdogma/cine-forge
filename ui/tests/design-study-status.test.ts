import assert from 'node:assert/strict'
import test from 'node:test'
import {
  formatDesignStudyFailureSummary,
  getDesignStudyFailureRows,
  getDesignStudyProgressText,
  isDesignStudyRoundActive,
} from '../src/lib/design-study-status.ts'
import type { DesignStudyGenerationFailure, DesignStudyRound } from '../src/lib/api/design-study.ts'

const failure: DesignStudyGenerationFailure = {
  provider: 'openai',
  model: 'gpt-image-1',
  message: 'content policy',
  operator_message: 'OpenAI Images failed while generating design-study image 2/4.',
  classification: 'policy_blocked',
  status_code: 400,
  request_id: 'req_123',
  error_code: 'content_policy_violation',
  error_type: 'invalid_request_error',
  failed_image_index: 2,
  prompt_sha256: 'abcdef1234567890',
  prompt_excerpt: 'Cinematic concept art of Brick Braddock.',
  created_at: '2026-04-30T07:00:00',
}

function round(overrides: Partial<DesignStudyRound>): DesignStudyRound {
  return {
    round_number: 2,
    prompt: 'prompt',
    model: 'gpt-image-1',
    entity_type: 'character',
    entity_id: 'character_brick_braddock',
    directive: null,
    positive_refs: [],
    negative_refs: [],
    seed_image_filename: null,
    sources_used: ['entity_bible'],
    learned_preferences_used: [],
    creative_brief_preview: null,
    count: 4,
    created_at: '2026-04-30T07:00:00',
    status: 'generating',
    failure: null,
    images: [],
    ...overrides,
  }
}

test('design-study progress text describes active and failed rounds', () => {
  assert.equal(isDesignStudyRoundActive(round({ status: 'generating' })), true)
  assert.equal(getDesignStudyProgressText(round({ status: 'generating', images: [] })), 'Generating 0 of 4 images')
  assert.equal(
    getDesignStudyProgressText(round({
      status: 'failed',
      failure,
      images: [{
        filename: 'design_study_r2_img1.jpg',
        decision: 'pending',
        guidance: null,
        prompt_used: 'prompt',
        model: 'gpt-image-1',
        round_number: 2,
        created_at: '2026-04-30T07:00:01',
      }],
    })),
    'Failed after 1 of 4 images',
  )
})

test('design-study failure summary preserves provider debug context', () => {
  assert.equal(
    formatDesignStudyFailureSummary(failure),
    'OpenAI Images failed on gpt-image-1 (policy blocked). Request ID: req_123.',
  )
  assert.deepEqual(getDesignStudyFailureRows(failure), [
    { label: 'Provider', value: 'OpenAI Images' },
    { label: 'Model', value: 'gpt-image-1' },
    { label: 'Classification', value: 'policy blocked' },
    { label: 'HTTP', value: '400' },
    { label: 'Request', value: 'req_123' },
    { label: 'Code', value: 'content_policy_violation' },
    { label: 'Prompt', value: 'abcdef123456' },
  ])
})
