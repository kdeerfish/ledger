import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import TagSelector from './TagSelector';

/**
 * 交易表单弹窗（添加/编辑）
 * 支持二级类别快速选择、自动建议、标签、模板
 */
export default function TransactionForm({ show, onClose, onSaved, editId }) {
  const [form, setForm] = useState({
    type: '支出', amount: '', category: '', subcategory: '',
    account: '', merchant: '', project: '', member: '', note: '',
    date: new Date().toISOString().slice(0, 16),
    tag_ids: [],
  });
  const [suggestions, setSuggestions] = useState({});
  const [quickSubs, setQuickSubs] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadSuggestions = useCallback(async () => {
    try {
      const res = await api.getSuggestions({ field: 'all' });
      if (res.data) setSuggestions(res.data);
    } catch (e) {}
  }, []);

  const loadQuickSubs = useCallback(async () => {
    try {
      const res = await api.getQuickCategories();
      if (res.data) setQuickSubs(res.data);
    } catch (e) {}
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const res = await api.getTemplates();
      if (res.data) setTemplates(res.data);
    } catch (e) {}
  }, []);

  useEffect(() => {
    if (show) {
      loadSuggestions();
      loadQuickSubs();
      loadTemplates();
    }
  }, [show, loadSuggestions, loadQuickSubs, loadTemplates]);

  useEffect(() => {
    if (show && !editId) {
      setForm({
        type: '支出', amount: '', category: '', subcategory: '',
        account: '', merchant: '', project: '', member: '', note: '',
        date: new Date().toISOString().slice(0, 16),
        tag_ids: [],
      });
    }
  }, [show, editId]);

  useEffect(() => {
    if (editId && show) {
      Promise.all([
        api.getTransaction(editId),
        api.getTags(),
      ]).then(([res, tagsRes]) => {
        if (res.data) {
          const t = res.data;
          const allTags = tagsRes.data || [];
          const excludeTag = allTags.find(tg => tg.name === '排除统计');
          const isExcluded = (t.tags || []).some(tg => tg.name === '排除统计');
          setForm({
            type: t.type || '支出',
            amount: t.amount || '',
            category: t.category || '',
            subcategory: t.subcategory || '',
            account: t.account || '',
            merchant: t.merchant || '',
            project: t.project || '',
            member: t.member || '',
            note: t.note || '',
            date: t.date ? t.date.replace(' ', 'T').slice(0, 16) : new Date().toISOString().slice(0, 16),
            tag_ids: (t.tags || []).map(tag => tag.id),
            _excludeFromStats: isExcluded,
            _excludeTagId: excludeTag?.id,
          });
        }
      }).catch(() => {});
    }
  }, [editId, show]);

  const set = (field, val) => setForm(prev => ({ ...prev, [field]: val }));

  const handleHide = async (field, value) => {
    if (!value) return;
    try {
      const res = await api.hideItem(field, value);
      // 直接从当前建议中移除
      const suggestionKey = field === 'category' ? 'categories'
        : field === 'subcategory' ? 'subcategories'
        : field + 's';
      setSuggestions(prev => ({
        ...prev,
        [suggestionKey]: (prev[suggestionKey] || []).filter(
          item => (item.name || item) !== value
        ),
      }));
      toast(`已隐藏 "${value}"`);
    } catch (e) {
      toast('隐藏失败: ' + e.message, 'danger');
    }
  };

  // 双向同步：toggle ↔ tag_ids
  useEffect(() => {
    if (form._excludeTagId && form.tag_ids) {
      const hasExcludeTag = form.tag_ids.includes(form._excludeTagId);
      if (form._excludeFromStats && !hasExcludeTag) {
        setForm(prev => ({ ...prev, _excludeFromStats: false }));
      } else if (!form._excludeFromStats && hasExcludeTag) {
        setForm(prev => ({ ...prev, _excludeFromStats: true }));
      }
    }
  }, [form.tag_ids, form._excludeTagId]);

  const handleQuickSub = (cat, sub) => {
    set('category', cat);
    set('subcategory', sub);
  };

  const applyTemplate = async (tmpl) => {
    setForm({
      type: tmpl.type || '支出',
      amount: tmpl.amount || '',
      category: tmpl.category || '',
      subcategory: tmpl.subcategory || '',
      account: tmpl.account || '',
      merchant: tmpl.merchant || '',
      project: tmpl.project || '',
      member: tmpl.member || '',
      note: tmpl.note || '',
      date: new Date().toISOString().slice(0, 16),
      tag_ids: [],
    });
    setShowTemplates(false);
    // 记录使用
    try { await api.useTemplate(tmpl.id); } catch (e) {}
  };

  const handleSave = async () => {
    const amount = parseFloat(form.amount);
    if (!amount || amount <= 0) {
      toast('金额必须大于零', 'warning');
      return;
    }
    setSaving(true);
    try {
      // 处理"排除统计"标签
      let tagIds = [...form.tag_ids];
      const excludeTagName = '排除统计';
      let excludeTagId = form._excludeTagId;

      // 确保"排除统计"标签存在
      if (form._excludeFromStats && !excludeTagId) {
        try {
          await api.createTag({ name: excludeTagName, color: '#6b7280' });
          const tagsRes = await api.getTags();
          if (tagsRes.data) {
            const t = tagsRes.data.find(tg => tg.name === excludeTagName);
            if (t) excludeTagId = t.id;
          }
        } catch (e) {}
      }

      if (form._excludeFromStats && excludeTagId && !tagIds.includes(excludeTagId)) {
        tagIds.push(excludeTagId);
      } else if (!form._excludeFromStats && excludeTagId) {
        tagIds = tagIds.filter(id => id !== excludeTagId);
      }

      const data = {
        ...form,
        amount,
        date: form.date ? form.date.replace('T', ' ') : undefined,
        tag_ids: tagIds,
        force: true,
      };
      // 清理内部字段
      delete data._excludeFromStats;
      delete data._excludeTagId;

      if (editId) {
        await api.updateTransaction(editId, data);
      } else {
        await api.addTransaction(data);
      }
      onSaved();
      onClose();
    } catch (e) {
      toast(e.message, 'danger');
    } finally {
      setSaving(false);
    }
  };

  if (!show) return null;

  const freq = suggestions.frequent || {};

  return (
    <div className="modal fade show d-block" tabIndex="-1" style={{ background: 'rgba(0,0,0,.5)' }}>
      <div className="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className={`bi ${editId ? 'bi-pencil' : 'bi-plus-circle'}`}></i>{' '}
              {editId ? `编辑交易 #${editId}` : '记一笔'}
            </h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            {/* 模板选择 */}
            {!editId && (
              <div className="mb-3">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <small className="text-muted">从模板选择：</small>
                  <button
                    className="btn btn-sm btn-outline-primary"
                    onClick={() => setShowTemplates(!showTemplates)}
                  >
                    <i className="bi bi-bookmark"></i> 模板
                  </button>
                </div>
                {showTemplates && templates.length > 0 && (
                  <div className="d-flex flex-wrap gap-2 mb-2">
                    {templates.map(tmpl => (
                      <div
                        key={tmpl.id}
                        className="template-card card p-2"
                        style={{ width: 140, cursor: 'pointer' }}
                        onClick={() => applyTemplate(tmpl)}
                      >
                        <small className="fw-bold">{tmpl.name}</small>
                        <small className="text-muted">
                          {tmpl.category}{tmpl.subcategory ? '/' + tmpl.subcategory : ''}
                        </small>
                        <small className={tmpl.type === '收入' ? 'amount-income' : 'amount-expense'}>
                          ¥{tmpl.amount || 0}
                        </small>
                      </div>
                    ))}
                  </div>
                )}
                {!showTemplates && templates.length > 0 && (
                  <div className="d-flex flex-wrap gap-1 mb-1">
                    {templates.slice(0, 4).map(tmpl => (
                      <button
                        key={tmpl.id}
                        className="quick-btn"
                        onClick={() => applyTemplate(tmpl)}
                      >
                        {tmpl.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="row g-3">
              {/* 类型 */}
              <div className="col-md-4">
                <label className="form-label">类型</label>
                <select className="form-select" value={form.type}
                  onChange={e => set('type', e.target.value)}>
                  <option value="支出">支出</option>
                  <option value="收入">收入</option>
                </select>
              </div>
              {/* 金额 */}
              <div className="col-md-4">
                <label className="form-label">金额 *</label>
                <input type="number" step="0.01" className="form-control"
                  value={form.amount} onChange={e => set('amount', e.target.value)}
                  placeholder="0.00" required />
              </div>
              {/* 日期 */}
              <div className="col-md-4">
                <label className="form-label">日期</label>
                <input type="datetime-local" className="form-control"
                  value={form.date} onChange={e => set('date', e.target.value)} />
              </div>

              {/* 类别 */}
              <div className="col-md-4">
                <label className="form-label">类别</label>
                <div className="input-group input-group-sm">
                  <input type="text" className="form-control" list="catList"
                    value={form.category} onChange={e => set('category', e.target.value)}
                    placeholder="如：食品酒水" />
                  {form.category && (
                    <button className="btn btn-outline-secondary" type="button"
                      onClick={() => handleHide('category', form.category)} title="隐藏此选项">
                      <i className="bi bi-eye-slash"></i>
                    </button>
                  )}
                </div>
                <datalist id="catList">
                  {(suggestions.categories || []).map(c => (
                    <option key={c.name} value={c.name} />
                  ))}
                </datalist>
              </div>

              {/* 子类别 */}
              <div className="col-md-4">
                <label className="form-label">子类别</label>
                <div className="input-group input-group-sm">
                  <input type="text" className="form-control" list="subcatList"
                    value={form.subcategory} onChange={e => set('subcategory', e.target.value)}
                    placeholder="如：水果" />
                  {form.subcategory && (
                    <button className="btn btn-outline-secondary" type="button"
                      onClick={() => handleHide('subcategory', form.subcategory)} title="隐藏此选项">
                      <i className="bi bi-eye-slash"></i>
                    </button>
                  )}
                </div>
                <datalist id="subcatList">
                  {(suggestions.subcategories || []).map(c => (
                    <option key={c.name} value={c.name} />
                  ))}
                </datalist>
              </div>

              {/* 账户 */}
              <div className="col-md-4">
                <label className="form-label">账户</label>
                <div className="input-group input-group-sm">
                  <input type="text" className="form-control" list="accList"
                    value={form.account} onChange={e => set('account', e.target.value)}
                    placeholder="如：微信" />
                  {form.account && (
                    <button className="btn btn-outline-secondary" type="button"
                      onClick={() => handleHide('account', form.account)} title="隐藏此选项">
                      <i className="bi bi-eye-slash"></i>
                    </button>
                  )}
                </div>
                <datalist id="accList">
                  {(suggestions.accounts || []).map(a => (
                    <option key={a.name} value={a.name} />
                  ))}
                </datalist>
              </div>

              {/* 商家 */}
              <div className="col-md-4">
                <label className="form-label">商家</label>
                <div className="input-group input-group-sm">
                  <input type="text" className="form-control" list="merchantList"
                    value={form.merchant} onChange={e => set('merchant', e.target.value)}
                    placeholder="如：美团" />
                  {form.merchant && (
                    <button className="btn btn-outline-secondary" type="button"
                      onClick={() => handleHide('merchant', form.merchant)} title="隐藏此选项">
                      <i className="bi bi-eye-slash"></i>
                    </button>
                  )}
                </div>
                <datalist id="merchantList">
                  {(suggestions.merchants || []).map(m => (
                    <option key={m.name} value={m.name} />
                  ))}
                </datalist>
              </div>

              {/* 项目 */}
              <div className="col-md-4">
                <label className="form-label">项目</label>
                <div className="input-group input-group-sm">
                  <input type="text" className="form-control" list="projectList"
                    value={form.project} onChange={e => set('project', e.target.value)}
                    placeholder="项目名称" />
                  {form.project && (
                    <button className="btn btn-outline-secondary" type="button"
                      onClick={() => handleHide('project', form.project)} title="隐藏此选项">
                      <i className="bi bi-eye-slash"></i>
                    </button>
                  )}
                </div>
                <datalist id="projectList">
                  {(suggestions.projects || []).map(p => (
                    <option key={p.name} value={p.name} />
                  ))}
                </datalist>
              </div>

              {/* 成员 */}
              <div className="col-md-4">
                <label className="form-label">成员</label>
                <div className="input-group input-group-sm">
                  <input type="text" className="form-control" list="memberList"
                    value={form.member} onChange={e => set('member', e.target.value)}
                    placeholder="如：本人" />
                  {form.member && (
                    <button className="btn btn-outline-secondary" type="button"
                      onClick={() => handleHide('member', form.member)} title="隐藏此选项">
                      <i className="bi bi-eye-slash"></i>
                    </button>
                  )}
                </div>
                <datalist id="memberList">
                  {(suggestions.members || []).map(m => (
                    <option key={m.name} value={m.name} />
                  ))}
                </datalist>
              </div>
            </div>

            {/* 子类别快速选择 */}
            {quickSubs.length > 0 && (
              <div className="mt-3">
                <small className="text-muted d-block mb-1">常用子类别：</small>
                <div className="d-flex flex-wrap">
                  {quickSubs.slice(0, 12).map((qs, i) => (
                    <button
                      key={i}
                      className={`quick-btn ${form.category === qs.category && form.subcategory === qs.subcategory ? 'active' : ''}`}
                      onClick={() => handleQuickSub(qs.category, qs.subcategory)}
                    >
                      {qs.category}/{qs.subcategory}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* 常用字段快速选择 */}
            <div className="row g-2 mt-2">
              {freq.accounts && freq.accounts.length > 0 && (
                <div className="col-6 col-md-3">
                  <small className="text-muted">常用账户：</small>
                  <div className="d-flex flex-wrap">
                    {freq.accounts.map(a => (
                      <button key={a.name} className="quick-btn btn-sm"
                        onClick={() => set('account', a.name)}>
                        {a.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {freq.members && freq.members.length > 0 && (
                <div className="col-6 col-md-3">
                  <small className="text-muted">常用成员：</small>
                  <div className="d-flex flex-wrap">
                    {freq.members.map(m => (
                      <button key={m.name} className="quick-btn btn-sm"
                        onClick={() => set('member', m.name)}>
                        {m.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Tags */}
            <div className="mt-3">
              <label className="form-label">
                <i className="bi bi-tag"></i> 标签
              </label>
              <TagSelector
                value={form.tag_ids}
                onChange={ids => set('tag_ids', ids)}
              />
              <div className="form-check form-switch mt-2">
                <input className="form-check-input" type="checkbox" id="excludeFromStats"
                  checked={form._excludeFromStats || false}
                  onChange={e => {
                    const checked = e.target.checked;
                    setForm(prev => {
                      const newState = { ...prev, _excludeFromStats: checked };
                      // 同步更新 tag_ids
                      if (prev._excludeTagId) {
                        if (checked && !prev.tag_ids.includes(prev._excludeTagId)) {
                          newState.tag_ids = [...prev.tag_ids, prev._excludeTagId];
                        } else if (!checked) {
                          newState.tag_ids = prev.tag_ids.filter(id => id !== prev._excludeTagId);
                        }
                      }
                      return newState;
                    });
                  }} />
                <label className="form-check-label small text-muted" htmlFor="excludeFromStats">
                  排除统计
                </label>
              </div>
            </div>

            {/* 备注 */}
            <div className="mt-3">
              <label className="form-label">备注</label>
              <textarea className="form-control" rows="2"
                value={form.note} onChange={e => set('note', e.target.value)}
                placeholder="备注信息"></textarea>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              取消
            </button>
            <button type="button" className="btn btn-ledger" onClick={handleSave}
              disabled={saving}>
              <i className="bi bi-check-lg"></i>{' '}
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// 简易 toast
function toast(msg, type = 'success') {
  const colors = { success: '#10b981', danger: '#ef4444', warning: '#f59e0b', info: '#3b82f6' };
  const icons = { success: 'bi-check-circle-fill', danger: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
  const container = document.querySelector('.toast-container') || (() => {
    const c = document.createElement('div');
    c.className = 'toast-container';
    document.body.appendChild(c);
    return c;
  })();
  const el = document.createElement('div');
  el.className = 'toast toast-ledger align-items-center border-0';
  el.innerHTML = `<div class="d-flex">
    <div class="toast-body"><i class="bi ${icons[type]}" style="color:${colors[type]}"></i> ${msg}</div>
    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
  </div>`;
  container.appendChild(el);
  const bs = new bootstrap.Toast(el, { delay: 3000 });
  bs.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}
window.toast = toast;
