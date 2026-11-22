const MAX_BUBBLES = 3
const SHORT_REPLY_LENGTH = 110
const SHORT_PARAGRAPH_LENGTH = 24
const LIST_START = /^(?:[-+*•]\s+|\d+[.)、]\s*|[一二三四五六七八九十]+、)/u

function length(text: string): number {
  return Array.from(text.replace(/\s/gu, '')).length
}

export function splitReply(content: string): string[] {
  const text = content.replace(/\r\n?/g, '\n').trim()
  if (!text) return []
  if (length(text) <= SHORT_REPLY_LENGTH) return [text]

  const paragraphs = text.split(/\n(?:[^\S\n]*\n)+/u)
  const bubbles: string[] = []
  for (const paragraph of paragraphs) {
    const previous = bubbles.at(-1)
    const lastLine = previous?.trimEnd().split('\n').at(-1)?.trimStart() ?? ''
    const listContinuation = LIST_START.test(paragraph.trimStart()) &&
      (LIST_START.test(lastLine) || /[:：](?:\*\*|__)?$/u.test(lastLine))
    if (previous && (listContinuation || length(paragraph) < SHORT_PARAGRAPH_LENGTH ||
        length(previous) < SHORT_PARAGRAPH_LENGTH)) {
      bubbles[bubbles.length - 1] = `${previous}\n\n${paragraph}`
    } else {
      bubbles.push(paragraph)
    }
  }

  while (bubbles.length > MAX_BUBBLES) {
    let mergeAt = 1
    for (let index = 2; index < bubbles.length - 1; index++) {
      if (length(bubbles[index]! + bubbles[index + 1]!) <
          length(bubbles[mergeAt]! + bubbles[mergeAt + 1]!)) {
        mergeAt = index
      }
    }
    // Keep the opening separate when it may contain an urgent action.
    bubbles.splice(mergeAt, 2, `${bubbles[mergeAt]}\n\n${bubbles[mergeAt + 1]}`)
  }

  return bubbles
}
