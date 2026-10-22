import { ArrowDown, ArrowUp, Pencil, Plus, Trash2 } from 'lucide-react'
import type { Topic } from '../api/courses'
import { childrenOf } from './topicUtils'

interface Props {
  topics: Topic[]
  canEdit: boolean
  selectedId?: string | null
  onSelect?: (topic: Topic) => void
  onAdd: (parent: Topic | null) => void
  onRename: (topic: Topic) => void
  onDelete: (topic: Topic) => void
  onMove: (topic: Topic, direction: -1 | 1) => void
}

export function TopicTree(props: Props) {
  const roots = childrenOf(props.topics, null)
  if (roots.length === 0) {
    return <p className="muted-text">No topics yet.{props.canEdit && ' Add the first one to get started.'}</p>
  }
  return <TopicList {...props} parentId={null} depth={0} />
}

function TopicList({ parentId, depth, ...props }: Props & { parentId: string | null; depth: number }) {
  const siblings = childrenOf(props.topics, parentId)
  if (siblings.length === 0) return null
  return (
    <ul className="topic-list" style={{ paddingLeft: depth === 0 ? 0 : 22 }}>
      {siblings.map((topic, index) => (
        <li key={topic.id}>
          <div className={`topic-row${props.selectedId === topic.id ? ' selected' : ''}`}>
            <button
              className="topic-title"
              onClick={() => props.onSelect?.(topic)}
              disabled={!props.onSelect}
            >
              {topic.title}
            </button>
            {props.canEdit && (
              <span className="topic-actions">
                <button className="icon-button" aria-label={`Move ${topic.title} up`} disabled={index === 0} onClick={() => props.onMove(topic, -1)}><ArrowUp size={14} /></button>
                <button className="icon-button" aria-label={`Move ${topic.title} down`} disabled={index === siblings.length - 1} onClick={() => props.onMove(topic, 1)}><ArrowDown size={14} /></button>
                <button className="icon-button" aria-label={`Add sub-topic to ${topic.title}`} onClick={() => props.onAdd(topic)}><Plus size={14} /></button>
                <button className="icon-button" aria-label={`Rename ${topic.title}`} onClick={() => props.onRename(topic)}><Pencil size={14} /></button>
                <button className="icon-button" aria-label={`Delete ${topic.title}`} onClick={() => props.onDelete(topic)}><Trash2 size={14} /></button>
              </span>
            )}
          </div>
          <TopicList {...props} parentId={topic.id} depth={depth + 1} />
        </li>
      ))}
    </ul>
  )
}
