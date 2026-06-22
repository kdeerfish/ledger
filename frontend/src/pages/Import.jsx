import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';

const FIELD_LABELS = {
  type: '交易类型', amount: '金额', date: '日期', category: '类别',
  subcategory: '子类别', account: '账户', merchant: '商家',
  member: '成员', project: '项目', note: '备注',
};

export default function Import() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({});
  const [tags, setTags] = useState([]);
  const [tagInput, setTagInput] = useState('');
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [existingTags, setExistingTags] = useState([]);

  useEffect(() => {
    api.getTags().then(res => {
      if (res.data) setExistingTags(res.data);
    }).catch(() => {});
  }, []);

  const handleFileSelect = useCallback((e) => {
    const f = e.target.files[0];
    if (f) {
      setFile(f);
      setError('');
    }
  }, []);

  const handlePreview = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.importPreview(formData);
      if (res.success && res.data) {
        setPreview(res.data);
        // 初始化映射
        const initMapping = {};
        Object.entries(res.data.mapping).forEach(([header, info]) => {
          initMapping[header] = info.target || '';
        });
        setMapping(initMapping);
        // 初始化标签
        setTags(res.data.suggested_tags || []);
        setStep(2);
      } else {
        setError(res.error || '预览失败');
      }
    } catch (err) {
      setError('网络错误: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [file]);

  const handleMappingChange = useCallback((header, target) => {
    setMapping(prev => ({ ...prev, [header]: target }));
  }, []);

  const handleAddTag = useCallback(() => {
    const t = tagInput.trim();
    if (t && !tags.includes(t)) {
      setTags(prev => [...prev, t]);
    }
    setTagInput('');
  }, [tagInput, tags]);

  const handleRemoveTag = useCallback((tag) => {
    setTags(prev => prev.filter(t => t !== tag));
  }, []);

  const handleExecute = useCallback(async () => {
    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('mapping', JSON.stringify(mapping));
    formData.append('tags', JSON.stringify(tags));
    formData.append('skip_duplicates', skipDuplicates.toString());
    if (preview?.detected_source) {
      formData.append('source', preview.detected_source);
    }

    try {
      const res = await api.importExecute(formData);
      if (res.success && res.data) {
        setResult(res.data);
        setStep(4);
      } else {
        setError(res.error || '导入失败');
      }
    } catch (err) {
      setError('网络错误: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [file, mapping, tags, skipDuplicates, preview]);

  const handleReset = useCallback(() => {
    setStep(1);
    setFile(null);
    setPreview(null);
    setMapping({});
    setTags([]);
    setResult(null);
    setError('');
  }, []);

  return (
    <div>
      <h4 className="mb-4"><i className="bi bi-cloud-upload"></i> 数据导入</h4>

      {/* 步骤指示器 */}
      <div className="d-flex mb-4">
        {['上传文件', '确认映射', '导入设置', '完成'].map((label, i) => (
          <div key={i} className="flex-fill text-center">
            <div className={`rounded-circle d-inline-flex align-items-center justify-content-center ${step > i + 1 ? 'bg-success text-white' : step === i + 1 ? 'bg-primary text-white' : 'bg-light text-muted'}`}
                 style={{ width: 32, height: 32, fontSize: 14 }}>
              {step > i + 1 ? <i className="bi bi-check"></i> : i + 1}
            </div>
            <div className="small mt-1">{label}</div>
          </div>
        ))}
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* Step 1: 上传文件 */}
      {step === 1 && (
        <div className="card">
          <div className="card-body text-center py-5">
            <i className="bi bi-file-earmark-spreadsheet" style={{ fontSize: 48, color: '#6c757d' }}></i>
            <h5 className="mt-3">选择 CSV 文件</h5>
            <p className="text-muted">支持 UTF-8、GBK 编码，最大 10MB</p>
            <input type="file" accept=".csv" className="form-control w-50 mx-auto mt-3"
                   onChange={handleFileSelect} />
            {file && (
              <div className="mt-3">
                <span className="badge bg-info">{file.name}</span>
                <span className="text-muted ms-2">({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            )}
            <div className="mt-4">
              <button className="btn btn-primary btn-lg" disabled={!file || loading}
                      onClick={handlePreview}>
                {loading ? <><span className="spinner-border spinner-border-sm me-2"></span>分析中...</> : <><i className="bi bi-search me-2"></i>分析文件</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: 确认映射 */}
      {step === 2 && preview && (
        <div>
          <div className="alert alert-info">
            <i className="bi bi-info-circle me-2"></i>
            检测到 <strong>{preview.detected_source}</strong> 格式，
            共 <strong>{preview.total_rows}</strong> 条记录，
            编码: {preview.encoding}
          </div>

          <div className="card mb-3">
            <div className="card-header"><strong>列映射</strong> <small className="text-muted">（可手动调整）</small></div>
            <div className="card-body p-0">
              <table className="table table-sm mb-0">
                <thead className="table-light">
                  <tr><th>原始列名</th><th>映射到</th><th>状态</th></tr>
                </thead>
                <tbody>
                  {preview.headers.map(header => {
                    const info = preview.mapping[header] || {};
                    const currentTarget = mapping[header] || '';
                    const isMapped = !!currentTarget;
                    return (
                      <tr key={header}>
                        <td><code>{header}</code></td>
                        <td>
                          <select className="form-select form-select-sm" style={{ width: 180 }}
                                  value={currentTarget}
                                  onChange={e => handleMappingChange(header, e.target.value)}>
                            <option value="">-- 不映射（存入其他信息）--</option>
                            {Object.entries(FIELD_LABELS).map(([key, label]) => (
                              <option key={key} value={key}>{label}</option>
                            ))}
                          </select>
                        </td>
                        <td>
                          {isMapped ? (
                            <span className="badge bg-success">
                              <i className="bi bi-check"></i> {FIELD_LABELS[currentTarget]}
                            </span>
                          ) : (
                            <span className="badge bg-warning text-dark">
                              <i className="bi bi-box"></i> 兜底保留
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 预览数据 */}
          {preview.preview_rows.length > 0 && (
            <div className="card mb-3">
              <div className="card-header"><strong>数据预览</strong> <small className="text-muted">（前 {preview.preview_rows.length} 行）</small></div>
              <div className="card-body p-0 table-responsive">
                <table className="table table-sm table-striped mb-0">
                  <thead className="table-light">
                    <tr>
                      {Object.values(FIELD_LABELS).map(label => <th key={label}>{label}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.preview_rows.map((row, i) => (
                      <tr key={i}>
                        {Object.keys(FIELD_LABELS).map(field => (
                          <td key={field}>{row[field] ?? ''}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="d-flex gap-2">
            <button className="btn btn-outline-secondary" onClick={() => setStep(1)}>
              <i className="bi bi-arrow-left"></i> 返回
            </button>
            <button className="btn btn-primary" onClick={() => setStep(3)}>
              下一步 <i className="bi bi-arrow-right"></i>
            </button>
          </div>
        </div>
      )}

      {/* Step 3: 导入设置 */}
      {step === 3 && preview && (
        <div>
          <div className="card mb-3">
            <div className="card-header"><strong>标签</strong></div>
            <div className="card-body">
              <div className="d-flex flex-wrap gap-2 mb-2">
                {tags.map(tag => (
                  <span key={tag} className="badge bg-primary d-flex align-items-center gap-1">
                    {tag}
                    <i className="bi bi-x" style={{ cursor: 'pointer' }} onClick={() => handleRemoveTag(tag)}></i>
                  </span>
                ))}
              </div>
              <div className="input-group" style={{ maxWidth: 300 }}>
                <input type="text" className="form-control form-control-sm" placeholder="添加标签..."
                       value={tagInput} onChange={e => setTagInput(e.target.value)}
                       onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), handleAddTag())} />
                <button className="btn btn-outline-primary btn-sm" onClick={handleAddTag}>添加</button>
              </div>
              {existingTags.length > 0 && (
                <div className="mt-2">
                  <small className="text-muted">已有标签：</small>
                  {existingTags.filter(t => !tags.includes(t.name)).slice(0, 10).map(t => (
                    <span key={t.id} className="badge bg-light text-dark ms-1" style={{ cursor: 'pointer' }}
                          onClick={() => setTags(prev => [...prev, t.name])}>
                      + {t.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="card mb-3">
            <div className="card-header"><strong>导入选项</strong></div>
            <div className="card-body">
              <div className="form-check">
                <input className="form-check-input" type="checkbox" id="skipDup"
                       checked={skipDuplicates} onChange={e => setSkipDuplicates(e.target.checked)} />
                <label className="form-check-label" htmlFor="skipDup">
                  跳过重复记录（同日+同类型+同金额+同类别）
                </label>
              </div>
              {preview.duplicate_estimate > 0 && (
                <div className="text-warning small mt-1">
                  <i className="bi bi-exclamation-triangle"></i> 预计有 {preview.duplicate_estimate} 条重复
                </div>
              )}
            </div>
          </div>

          <div className="alert alert-secondary">
            将导入 <strong>{preview.total_rows - preview.duplicate_estimate}</strong> 条记录，
            标签: {tags.length > 0 ? tags.join(', ') : '无'}
          </div>

          <div className="d-flex gap-2">
            <button className="btn btn-outline-secondary" onClick={() => setStep(2)}>
              <i className="bi bi-arrow-left"></i> 返回
            </button>
            <button className="btn btn-success btn-lg" onClick={handleExecute} disabled={loading}>
              {loading ? <><span className="spinner-border spinner-border-sm me-2"></span>导入中...</> : <><i className="bi bi-check-circle me-2"></i>确认导入</>}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: 完成 */}
      {step === 4 && result && (
        <div className="text-center py-4">
          <i className="bi bi-check-circle-fill text-success" style={{ fontSize: 64 }}></i>
          <h4 className="mt-3">导入完成！</h4>
          <div className="mt-3">
            <div className="row justify-content-center">
              <div className="col-auto">
                <div className="card px-4 py-2">
                  <div className="text-muted small">成功导入</div>
                  <div className="fs-3 fw-bold text-success">{result.imported}</div>
                </div>
              </div>
              {result.skipped > 0 && (
                <div className="col-auto">
                  <div className="card px-4 py-2">
                    <div className="text-muted small">跳过</div>
                    <div className="fs-3 fw-bold text-warning">{result.skipped}</div>
                  </div>
                </div>
              )}
              {result.duplicates_found > 0 && (
                <div className="col-auto">
                  <div className="card px-4 py-2">
                    <div className="text-muted small">重复</div>
                    <div className="fs-3 fw-bold text-secondary">{result.duplicates_found}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
          {result.tags_applied && result.tags_applied.length > 0 && (
            <div className="mt-3">
              标签: {result.tags_applied.map(t => <span key={t} className="badge bg-primary ms-1">{t}</span>)}
            </div>
          )}
          {result.errors && result.errors.length > 0 && (
            <div className="alert alert-warning mt-3 text-start" style={{ maxWidth: 500, margin: '0 auto' }}>
              <strong>部分错误：</strong>
              <ul className="mb-0">
                {result.errors.slice(0, 5).map((err, i) => <li key={i}>{err}</li>)}
              </ul>
            </div>
          )}
          <div className="mt-4">
            <button className="btn btn-primary me-2" onClick={handleReset}>
              <i className="bi bi-plus-circle me-1"></i> 继续导入
            </button>
            <a href="/transactions" className="btn btn-outline-secondary">
              <i className="bi bi-list-ul me-1"></i> 查看交易
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
