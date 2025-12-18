import { memo } from 'react';

interface FormattedMessageProps {
  content: string;
  role: 'user' | 'assistant';
}

const FormattedMessage = memo(({ content, role }: FormattedMessageProps) => {
  // Apply markdown formatting to text
  const applyMarkdownFormatting = (text: string): (string | JSX.Element)[] => {
    const parts: (string | JSX.Element)[] = [];
    let remaining = text;
    let key = 0;

    // Pattern to match: **bold**, *italic*, __bold__, _italic_
    const markdownPattern = /(\*\*([^*]+)\*\*|\*([^*]+)\*|__([^_]+)__|_([^_]+)_)/g;
    let match;
    let lastIndex = 0;

    while ((match = markdownPattern.exec(remaining)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push(remaining.substring(lastIndex, match.index));
      }

      // Determine what was matched and format accordingly
      const fullMatch = match[0];
      const boldDoubleStar = match[2];
      const italicStar = match[3];
      const boldDoubleUnderscore = match[4];
      const italicUnderscore = match[5];

      if (boldDoubleStar || boldDoubleUnderscore) {
        // Bold text
        parts.push(
          <strong key={`bold-${key++}`} className="font-bold text-gray-900 dark:text-slate-100">
            {boldDoubleStar || boldDoubleUnderscore}
          </strong>
        );
      } else if (italicStar || italicUnderscore) {
        // Italic text
        parts.push(
          <em key={`italic-${key++}`} className="italic">
            {italicStar || italicUnderscore}
          </em>
        );
      }

      lastIndex = match.index + fullMatch.length;
    }

    // Add remaining text
    if (lastIndex < remaining.length) {
      parts.push(remaining.substring(lastIndex));
    }

    return parts.length > 0 ? parts : [text];
  };

  // Format the content for better display
  const formatContent = (text: string) => {
    // Split by code blocks
    const parts = text.split(/```(\w*)\n?([\s\S]*?)```/g);
    const formatted: JSX.Element[] = [];

    for (let i = 0; i < parts.length; i++) {
      if (i % 3 === 0) {
        // Regular text
        if (parts[i].trim()) {
          // Split by inline code
          const inlineParts = parts[i].split(/`([^`]+)`/g);
          const inlineFormatted = inlineParts.map((part, idx) => {
            if (idx % 2 === 1) {
              // Inline code
              return (
                <code
                  key={`inline-${i}-${idx}`}
                  className="px-2 py-0.5 bg-gray-100 dark:bg-slate-700 rounded text-sm font-mono text-primary-600 dark:text-primary-400"
                >
                  {part}
                </code>
              );
            }
            // Regular text - apply markdown formatting and preserve line breaks
            const lines = part.split('\n');
            return (
              <span key={`text-${i}-${idx}`}>
                {lines.map((line, lineIdx) => (
                  <span key={lineIdx}>
                    {applyMarkdownFormatting(line)}
                    {lineIdx < lines.length - 1 && <br />}
                  </span>
                ))}
              </span>
            );
          });
          formatted.push(
            <div key={`block-${i}`} className="mb-4 leading-relaxed">
              {inlineFormatted}
            </div>
          );
        }
      } else if (i % 3 === 1) {
        // Language identifier
        const language = parts[i] || 'text';
        const code = parts[i + 1];
        formatted.push(
          <div key={`code-${i}`} className="mb-4 rounded-lg overflow-hidden">
            <div className="bg-slate-800 dark:bg-slate-900 px-4 py-2 text-xs text-slate-400 font-mono border-b border-slate-700">
              {language}
            </div>
            <pre className="bg-slate-900 dark:bg-black p-4 overflow-x-auto">
              <code className="text-sm font-mono text-slate-100">{code}</code>
            </pre>
          </div>
        );
      }
    }

    return formatted;
  };

  // Format lists (bullets and numbered)
  const formatLists = (elements: JSX.Element[]) => {
    return elements.map((element, idx) => {
      if (element.type === 'div' && element.props.children) {
        const content = element.props.children;
        if (typeof content === 'string' || Array.isArray(content)) {
          const text = Array.isArray(content) 
            ? content.map(c => typeof c === 'string' ? c : c.props?.children || '').join('')
            : content;
          
          // Check for bullet points
          if (typeof text === 'string' && /^[•\-\*]\s/.test(text)) {
            return (
              <li key={idx} className="ml-4 mb-2">
                {text.replace(/^[•\-\*]\s/, '')}
              </li>
            );
          }
          
          // Check for numbered lists
          if (typeof text === 'string' && /^\d+\.\s/.test(text)) {
            return (
              <li key={idx} className="ml-4 mb-2 list-decimal">
                {text.replace(/^\d+\.\s/, '')}
              </li>
            );
          }
        }
      }
      return element;
    });
  };

  const formattedElements = formatContent(content);
  const withLists = formatLists(formattedElements);

  return (
    <div
      className={`prose prose-sm max-w-none ${
        role === 'assistant'
          ? 'dark:prose-invert prose-pre:bg-slate-900 prose-code:text-primary-600 dark:prose-code:text-primary-400'
          : 'dark:prose-invert'
      }`}
    >
      {withLists}
    </div>
  );
});

FormattedMessage.displayName = 'FormattedMessage';

export default FormattedMessage;
