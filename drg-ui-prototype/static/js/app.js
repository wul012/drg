document.addEventListener('DOMContentLoaded', () => {
    const flashes = Array.from(document.querySelectorAll('.flash'));
    if (flashes.length > 0) {
        window.setTimeout(() => {
            flashes.forEach((item) => {
                item.style.opacity = '0';
                item.style.transform = 'translateY(-4px)';
                item.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
                window.setTimeout(() => item.remove(), 250);
            });
        }, 2600);
    }

    const parseCaseJsonButton = document.querySelector('#parse_case_json');
    if (parseCaseJsonButton) {
        parseCaseJsonButton.addEventListener('click', () => {
            const jsonInput = document.querySelector('#case_json');
            const message = document.querySelector('#case_json_parse_message');
            const setMessage = (text, isError = false) => {
                if (!message) {
                    return;
                }
                message.textContent = text;
                message.classList.toggle('error-text', isError);
            };
            try {
                const payload = JSON.parse(jsonInput.value || '{}');
                const primary = payload['主要诊断'] || {};
                const procedure = payload['主要手术'] || {};
                const secondaryList = Array.isArray(payload['次要诊断列表']) ? payload['次要诊断列表'] : [];
                const otherProcedureList = Array.isArray(payload['其他手术列表']) ? payload['其他手术列表'] : [];
                const patientNameInput = document.querySelector('#patient_name');
                if (patientNameInput && !patientNameInput.value) {
                    patientNameInput.value = payload['姓名'] || payload['患者姓名'] || '';
                }
                document.querySelector('#primary_diagnosis_name').value = primary['疾病名称'] || '';
                document.querySelector('#primary_diagnosis_code').value = primary['疾病编码'] || '';
                document.querySelector('#procedure_name').value = procedure['手术名称'] || '';
                document.querySelector('#procedure_code').value = procedure['手术编码'] || '';
                document.querySelector('#secondary_diagnosis_list').value = JSON.stringify(secondaryList, null, 2);
                document.querySelector('#other_procedure_list').value = JSON.stringify(otherProcedureList, null, 2);
                setMessage('已解析到表单，确认后再执行入组。');
            } catch (error) {
                setMessage(`JSON格式不正确：${error.message}`, true);
            }
        });
    }

    const analysisForm = document.querySelector('#analysis_form');
    const analysisResult = document.querySelector('#analysis_result');
    if (analysisForm && analysisResult) {
        const createCard = (title) => {
            const card = document.createElement('div');
            card.className = 'item-card analysis-result-card';
            const heading = document.createElement('h4');
            heading.textContent = title;
            card.appendChild(heading);
            return card;
        };

        const renderTextCard = (title, content) => {
            const card = createCard(title);
            const text = document.createElement('pre');
            text.className = 'analysis-document-text';
            text.textContent = content || '';
            card.appendChild(text);
            return card;
        };

        const renderTestCasesCard = (testCases) => {
            const card = createCard('测试用例');
            const list = document.createElement('div');
            list.className = 'analysis-test-case-list';
            (Array.isArray(testCases) ? testCases : []).forEach((item) => {
                const block = document.createElement('div');
                block.className = 'analysis-test-case';
                const title = document.createElement('strong');
                title.textContent = `${item.case_code || ''} ${item.feature || ''}`.trim();
                const detail = document.createElement('p');
                detail.textContent = `前置：${item.precondition_text || ''}\n步骤：${item.steps_text || ''}\n预期：${item.expected_text || ''}`;
                block.appendChild(title);
                block.appendChild(detail);
                list.appendChild(block);
            });
            card.appendChild(list);
            return card;
        };

        const setResultMessage = (message, isError = false) => {
            analysisResult.innerHTML = '';
            const card = createCard(isError ? '生成失败' : '生成中');
            const text = document.createElement('p');
            text.className = isError ? 'error-text' : '';
            text.textContent = message;
            card.appendChild(text);
            analysisResult.appendChild(card);
        };

        const renderAnalysisResult = (payload) => {
            const documentContents = payload.document_contents || {};
            analysisResult.innerHTML = '';
            analysisResult.appendChild(renderTextCard('需求分析文档', documentContents['需求分析文档']));
            analysisResult.appendChild(renderTextCard('架构设计文档', documentContents['架构设计文档']));
            analysisResult.appendChild(renderTextCard('测试文档', documentContents['测试文档']));
            analysisResult.appendChild(renderTestCasesCard(payload.test_cases));
        };

        analysisForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const submitButton = analysisForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton ? submitButton.textContent : '';
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = '正在调用模型...';
            }
            setResultMessage('正在调用大模型生成文档，请稍候。');

            try {
                const response = await fetch(analysisForm.action || window.location.href, {
                    method: 'POST',
                    body: new FormData(analysisForm),
                    headers: {
                        'X-Requested-With': 'fetch',
                    },
                });
                const payload = await response.json();
                if (!response.ok || !payload.ok) {
                    throw new Error(payload.message || '生成失败，请稍后重试。');
                }
                renderAnalysisResult(payload);
            } catch (error) {
                setResultMessage(error.message || '生成失败，请稍后重试。', true);
            } finally {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = originalButtonText;
                }
            }
        });
    }
});
