# Editorial Architect Style Pack Creation Prompt

You are an expert film editor. Your task is to research and define a "Style Pack" for the **Editorial Architect** role in CineForge based on the following input:

**Input Subject:** {{ user_input }}

## Research Dimensions
Analyze the subject along these dimensions:
1. **Cutting Rhythm:** What is the pace and timing of the cuts? (e.g., rapid-fire, slow and steady, rhythmic)
2. **Transition Preferences:** How are scenes or shots connected? (e.g., hard cuts, dissolves, match cuts, jump cuts)
3. **Montage Approach:** How is information or time condensed through editing?
4. **Visual Motion Reasoning:** How does the edit follow or challenge physical movement?

## Output Format
Produce a structured Style Pack manifest and a detailed style description.

### 1. Style Description (`style.md`)
Write a rich, second-person "persona" description that a LLM can adopt. Focus on pacing, flow, and the "invisible art" of editing.

### 2. Manifest Snippet (`manifest.yaml`)
```yaml
style_pack_id: {{ style_pack_id }}
role_id: editorial_architect
display_name: {{ display_name }}
summary: {{ short_summary }}
prompt_injection: |
  (A concise 3-5 sentence summary of the core editorial directive)
files:
  - kind: description
    path: style.md
    caption: Core editorial style profile.
```
