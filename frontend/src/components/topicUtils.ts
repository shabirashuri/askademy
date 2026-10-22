import type { Topic } from '../api/courses'

export function childrenOf(topics: Topic[], parentId: string | null): Topic[] {
  return topics
    .filter((t) => t.parent_topic_id === parentId)
    .sort((a, b) => a.position - b.position || a.title.localeCompare(b.title))
}
