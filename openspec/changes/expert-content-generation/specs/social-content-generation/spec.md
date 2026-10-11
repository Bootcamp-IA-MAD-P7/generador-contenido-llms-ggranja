# Social Content Generation

## Purpose

Define how the product guides a content manager from incomplete business information to truthful, editable, platform-adapted social content.

The system MUST apply each ADDED requirement below.

## ADDED Requirements


### Requirement: Guided business and audience discovery

The system SHALL identify which required facts are missing or ambiguous before it drafts content that depends on them.

#### Scenario: Offer or topic is missing
- GIVEN a user asks for a post without a usable offer or topic
- WHEN the system prepares the generation brief
- THEN it asks a focused question before creating business-specific claims.

#### Scenario: Audience is unknown
- GIVEN the user cannot define the target audience
- WHEN the agent conducts discovery
- THEN it asks about real customer situations, questions, purchase/use roles, objections, and examples
- AND it labels resulting audience conclusions as inferred until the user confirms them.

#### Scenario: Existing business facts are available
- GIVEN approved profile facts are available from the business context
- WHEN the agent asks follow-up questions
- THEN it reuses those facts and asks only for material missing or changed information.

#### Scenario: Consequential uncertainty remains
- GIVEN an unverified assumption could change the audience, offer promise, or CTA
- WHEN the draft depends on that assumption
- THEN the system asks for validation or explicitly labels the assumption and avoids stating it as fact.

### Requirement: Evidence and assumption handling

The system SHALL distinguish user-confirmed or approved business facts from inference and unknown information.

#### Scenario: Claim lacks evidence
- GIVEN a proposed claim has no support in the user brief or approved business context
- WHEN copy is generated
- THEN the system omits the claim or asks for evidence
- AND SHALL NOT invent a statistic, benefit, testimonial, result, deadline, quantity, credential, or guarantee.

#### Scenario: Persuasion uses proof or scarcity
- GIVEN social proof, anchoring, reciprocity, urgency, or scarcity is considered
- WHEN the copy uses that device
- THEN the device is relevant to the post and grounded in a real, approved fact.

### Requirement: Goal-led content strategy

The system SHALL select a message angle and CTA based on an explicit or user-confirmed goal and the available audience insight.

#### Scenario: Goal is missing
- GIVEN the user's goal is not known and different goals would lead to materially different posts
- WHEN the agent plans the content
- THEN it asks the user to select or describe the intended outcome.

#### Scenario: Strategy is selected
- GIVEN the goal and enough audience/offer context are known
- WHEN the agent creates a plan
- THEN it maps goal, audience situation, need/desire/objection, core message, platform, format, angle and CTA.

#### Scenario: Copy formula is applicable
- GIVEN one or more copy approaches or formulas could fit the goal
- WHEN the agent drafts
- THEN it uses an appropriate formula as an optional scaffold
- AND is not required to force a formula or name it in the final output.

### Requirement: reviewer-selected copy formula

The drafting API and review interface MUST allow a reviewer to select AIDA,
PAS, 4 Cs, BAB, 4 Ps or an open loop as an optional copy scaffold. A selected
formula MUST be reflected in the draft response and MUST NOT add facts or
claims.

#### Scenario: reviewer selects a formula

- GIVEN an editable draft and a selected copy formula
- WHEN the reviewer requests generation or regeneration
- THEN the API uses that formula as optional structural guidance
- AND the response identifies the approach, formula and rationale.

#### Scenario: selected formula needs evidence that the brief lacks

- GIVEN PAS, BAB or 4 Ps is selected
- AND the brief has no confirmed facts
- WHEN the API returns the draft
- THEN the interface warns that confirmed facts are missing
- AND the draft uses only general framing without invented proof or outcomes.

### Requirement: Adaptive interview

The system SHALL ask the minimum useful follow-up questions needed to generate an accurate draft.

#### Scenario: Several facts are missing
- GIVEN more than one detail is unknown
- WHEN the agent asks follow-ups
- THEN it prioritizes the questions that materially affect content quality and avoids repeating known information.

#### Scenario: User prefers a provisional draft
- GIVEN only non-critical details are unknown
- WHEN the user wants to proceed
- THEN the system may produce an editable draft with the assumptions clearly labeled.

### Requirement: Instagram and Facebook adaptation

The system SHALL generate or adapt content for the selected initial Meta channel or channels, subject to the canonical MVP scope.

#### Scenario: Both channels are selected
- GIVEN Instagram and Facebook are both requested
- WHEN content is generated
- THEN the system preserves the supported core message and adapts the copy and presentation for each platform rather than assuming identical text is optimal.

#### Scenario: Unsupported platform detail is uncertain
- GIVEN a technical format, placement, dimension, limit or safe zone may have changed or is not verified
- WHEN the system prepares visual guidance
- THEN it treats the value as provisional and requests or relies on current official platform guidance before enforcing it.

### Requirement: Supported post-format package

The proposed content formats are single-image feed posts, carousels and Reels. Stories are deferred. The final MVP subset SHALL match the human-approved canonical scope before implementation.

#### Scenario: Single-image package
- GIVEN an image feed post is selected
- WHEN the system returns a draft
- THEN it provides a concise, complementary image-text suggestion and visual direction along with the caption and CTA.

#### Scenario: Carousel package
- GIVEN a carousel is within approved scope and selected
- WHEN the system returns a draft
- THEN it provides a cover hook, a coherent per-slide progression, a closing CTA, and optional continuation cue.

#### Scenario: Reel package
- GIVEN a Reel is within approved scope and selected
- WHEN the system returns a draft
- THEN it provides a concise scene/script structure, readable on-screen text, caption and sound-off subtitle guidance.

#### Scenario: Story is requested in this phase
- GIVEN Stories are deferred
- WHEN the user requests a Story package
- THEN the system explains that the format is not part of the agreed initial slice and offers an in-scope alternative.

### Requirement: Copy and visual guidance

The system SHALL use copywriting and design knowledge as contextual guidance rather than guaranteed-performance rules.

#### Scenario: Caption is generated
- GIVEN enough facts are available
- WHEN the system writes a caption
- THEN it normally supplies a first-line hook, concise scannable body, direct CTA, and only functional emojis/hashtags/keywords appropriate to the brand and platform.

#### Scenario: Visual direction is generated
- GIVEN a visual asset or design concept is requested
- WHEN the system provides direction
- THEN it prioritizes mobile legibility, adequate contrast, one primary focal point, brand coherence and relevant accessibility guidance.

#### Scenario: Performance statistic is not verified
- GIVEN a numeric engagement claim or universal design rule is not supported by a verified source
- WHEN the system explains its recommendation
- THEN it presents the advice as a heuristic or omits the statistic; it SHALL NOT promise increased clicks, reach or conversion.

### Requirement: Brand coherence and accessibility

The system SHALL use approved brand guidance when available and provide accessible content cues where applicable.

#### Scenario: Brand profile exists
- GIVEN brand voice and visual identity are available
- WHEN content is drafted
- THEN the tone, vocabulary, palette, typography and logo guidance follow that profile.

#### Scenario: Brand profile is incomplete
- GIVEN no usable brand rules are available
- WHEN content is drafted
- THEN the system uses a clear neutral style and marks any material creative assumption for user review.

#### Scenario: Image or video content is generated
- GIVEN the output includes an image or video package
- WHEN the result is returned
- THEN it includes alt-text guidance for important images and readable subtitle guidance for video.

### Requirement: Structured editable output

The system SHALL return an output package that separates strategy, copy, visual guidance and unresolved assumptions.

#### Scenario: Draft is ready
- GIVEN required facts are confirmed or safely bounded
- WHEN the agent returns the post
- THEN the output includes platform(s), format, goal, audience status, core message, caption, CTA, relevant visual guidance, and assumptions or follow-up needs.

#### Scenario: A/B testing is useful
- GIVEN the user asks for variants or a meaningful test can be described
- WHEN the agent provides variants
- THEN it changes a defined element such as hook or CTA and states a test hypothesis and one primary objective-aligned metric.

### Requirement: Human publication control

The content generator SHALL preserve the existing human approval rule for publishing to Instagram.

#### Scenario: Instagram post is ready to publish
- GIVEN a generated draft is connected to the Instagram publishing flow
- WHEN publication is requested
- THEN the user must review and explicitly confirm the exact content before publication.

#### Scenario: Voice mode requests publication
- GIVEN an Instagram draft was created or revised through voice interaction
- WHEN publication is requested
- THEN voice interaction alone does not count as approval; explicit human confirmation is required.

## Scope and verification note

This contract does not authorize direct Facebook publishing, unattended or scheduled publication, multi-business administration, or Stories. It does not change the canonical MVP scope until the format-set conflict in the proposal is resolved and the contract is approved.
