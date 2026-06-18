import { useState, useEffect, useRef } from 'react';
import { api } from '../api';

/**
 * 标签选择器组件
 * 支持输入搜索、多选、创建新标签
 */
export default function TagSelector({ value = [], onChange }) {
  const [tags, setTags] = useState([]);
  const [input, setInput] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    api.getTags().then(res => {
      if (res.data) setTags(res.data);
    }).catch(() => {});
  }, []);

  const filtered = tags.filter(t =>
    !value.includes(t.id) &&
    t.name.toLowerCase().includes(input.toLowerCase())
  );

  const selectedTags = tags.filter(t => value.includes(t.id));

  const handleSelect = async (tag) => {
    if (!value.includes(tag.id)) {
      onChange([...value, tag.id]);
    }
    setInput('');
    setShowDropdown(false);
    inputRef.current?.focus();
  };

  const handleRemove = (tagId) => {
    onChange(value.filter(id => id !== tagId));
  };

  const handleCreate = async () => {
    const name = input.trim();
    if (!name) return;
    try {
      const res = await api.createTag({ name });
      const newTag = { id: res.data.id, name, color: '#6366f1' };
      setTags([...tags, newTag]);
      handleSelect(newTag);
    } catch (e) {
      // 可能已存在
      api.getTags().then(r => {
        if (r.data) setTags(r.data);
      });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered.length > 0) {
        handleSelect(filtered[0]);
      } else if (input.trim()) {
        handleCreate();
      }
    } else if (e.key === 'Backspace' && !input && value.length > 0) {
      handleRemove(value[value.length - 1]);
    }
  };

  return (
    <div className="tag-selector" onClick={() => inputRef.current?.focus()}>
      {selectedTags.map(tag => (
        <span
          key={tag.id}
          className="tag-badge"
          style={{ background: tag.color + '22', color: tag.color, border: `1px solid ${tag.color}44` }}
        >
          {tag.name}
          <i
            className="bi bi-x ms-1"
            style={{ cursor: 'pointer' }}
            onClick={(e) => { e.stopPropagation(); handleRemove(tag.id); }}
          ></i>
        </span>
      ))}
      <div style={{ position: 'relative', flex: 1, minWidth: 80 }}>
        <input
          ref={inputRef}
          type="text"
          className="form-control border-0 p-0"
          style={{ boxShadow: 'none', background: 'transparent', height: 'auto' }}
          placeholder={value.length === 0 ? '输入标签名...' : ''}
          value={input}
          onChange={e => { setInput(e.target.value); setShowDropdown(true); }}
          onFocus={() => setShowDropdown(true)}
          onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
          onKeyDown={handleKeyDown}
        />
        {showDropdown && (filtered.length > 0 || input.trim()) && (
          <div
            className="dropdown-menu show"
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              zIndex: 1050,
              minWidth: 180,
              maxHeight: 200,
              overflow: 'auto',
              fontSize: '.85rem',
            }}
          >
            {filtered.map(tag => (
              <button
                key={tag.id}
                className="dropdown-item d-flex align-items-center gap-2"
                onMouseDown={() => handleSelect(tag)}
                type="button"
              >
                <span
                  style={{
                    display: 'inline-block',
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: tag.color,
                  }}
                ></span>
                {tag.name}
              </button>
            ))}
            {input.trim() && filtered.length === 0 && (
              <button
                className="dropdown-item text-primary"
                onMouseDown={handleCreate}
                type="button"
              >
                <i className="bi bi-plus-circle"></i> 创建 "{input.trim()}"
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
