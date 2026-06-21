### How to Run Locally Now:

Simply open your terminal in the project root folder and execute one of the following:

**Using Python directly (Cross-Platform):**

<pre><div node="[object Object]" class="relative whitespace-pre-wrap word-break-all my-2 rounded-xl bg-muted border"><div class="min-h-7 relative box-border flex flex-row items-center justify-between rounded-t border-b border-border px-2 py-0.5"><div class="font-sans text-sm text-muted-foreground">bash</div><div class="flex flex-row gap-2 justify-end"></div></div><div class="p-3"><div class="w-full h-full text-xs cursor-text"><div class="code-block"><div class="code-line" data-line-number="1" data-line-start="1" data-line-end="1"><div class="line-content"><span class="mtk16">python</span><span class="mtk1"></span><span class="mtk12">run.py</span></div></div></div></div></div></div></pre>

**Using PowerShell (Windows):**

<pre><div node="[object Object]" class="relative whitespace-pre-wrap word-break-all my-2 rounded-xl bg-muted border"><div class="min-h-7 relative box-border flex flex-row items-center justify-between rounded-t border-b border-border px-2 py-0.5"><div class="font-sans text-sm text-muted-foreground">powershell</div><div class="flex flex-row gap-2 justify-end"></div></div><div class="p-3"><div class="w-full h-full text-xs cursor-text"><div class="code-block"><div class="code-line" data-line-number="1" data-line-start="1" data-line-end="1"><div class="line-content"><span class="mtk1">.</span><span class="mtk3">/</span><span class="mtk1">start.ps1</span></div></div></div></div></div></div></pre>

**Using Bash (Linux/macOS):**

<pre><div node="[object Object]" class="relative whitespace-pre-wrap word-break-all my-2 rounded-xl bg-muted border"><div class="min-h-7 relative box-border flex flex-row items-center justify-between rounded-t border-b border-border px-2 py-0.5"><div class="font-sans text-sm text-muted-foreground">bash</div><div class="flex flex-row gap-2 justify-end"></div></div><div class="p-3"><div class="w-full h-full text-xs cursor-text"><div class="code-block"><div class="code-line" data-line-number="1" data-line-start="1" data-line-end="1"><div class="line-content"><span class="mtk16">./start.sh</span></div></div></div></div></div></div></pre>


### 1. 💬 Conversational CLI Client (Recommended)

I created ![](vscode-file://vscode-app/c:/Users/hp/AppData/Local/Programs/Antigravity%20IDE/resources/app/extensions/theme-symbols/src/icons/files/python.svg)

cli.py in the root folder. You can run an interactive conversation loop in the terminal where you can type any query, see retrieved document citations, and receive responses with full conversation context.

**How to run:**

<pre><div node="[object Object]" class="relative whitespace-pre-wrap word-break-all my-2 rounded-xl bg-muted border"><div class="min-h-7 relative box-border flex flex-row items-center justify-between rounded-t border-b border-border px-2 py-0.5"><div class="font-sans text-sm text-muted-foreground">powershell</div><div class="flex flex-row gap-2 justify-end"></div></div><div class="p-3"><div class="w-full h-full text-xs cursor-text"><div class="code-block"><div class="code-line" data-line-number="1" data-line-start="1" data-line-end="1"><div class="line-content"><span class="mtk1">python cli.py</span></div></div></div></div></div></div></pre>

---

### 2. 🧪 Automated Rigorous Evaluation Suite

This executes the 11 complex legal QA scenarios (Category rights, IPC exceptions, pronoun follow-ups, memory personalization, and safety filters), scores them using an LLM-as-a-judge, and appends the detailed results to the test execution history log.

**How to run:**

<pre><div node="[object Object]" class="relative whitespace-pre-wrap word-break-all my-2 rounded-xl bg-muted border"><div class="min-h-7 relative box-border flex flex-row items-center justify-between rounded-t border-b border-border px-2 py-0.5"><div class="font-sans text-sm text-muted-foreground">powershell</div><div class="flex flex-row gap-2 justify-end"></div></div><div class="p-3"><div class="w-full h-full text-xs cursor-text"><div class="code-block"><div class="code-line" data-line-number="1" data-line-start="1" data-line-end="1"><div class="line-content"><span class="mtk5"># On Windows PowerShell:</span></div></div><div class="code-line" data-line-number="2" data-line-start="2" data-line-end="2"><div class="line-content"><span class="mtk10">$env:PYTHONPATH</span><span class="mtk3">=</span><span class="mtk12">"."</span><span class="mtk1"> ; python tests</span><span class="mtk3">/</span><span class="mtk1">run_rigorous_tests.py</span></div></div><div class="code-line" data-line-number="3" data-line-start="3" data-line-end="3"><div class="line-content"><span class="mtk1"></span></div></div><div class="code-line" data-line-number="4" data-line-start="4" data-line-end="4"><div class="line-content"><span class="mtk5"># On Bash (macOS/Linux):</span></div></div><div class="code-line" data-line-number="5" data-line-start="5" data-line-end="5"><div class="line-content"><span class="mtk1">PYTHONPATH</span><span class="mtk3">=</span><span class="mtk12">"."</span><span class="mtk1"> python tests</span><span class="mtk3">/</span><span class="mtk1">run_rigorous_tests.py</span></div></div></div></div></div></div></pre>

---

### 3. 🛡️ Safety / Adversarial Test Runner

Runs queries with adversarial intent (such as illegal bypasses, drug offenses, or tax evasion) and logs the safety alignment outputs and document structures.

**How to run:**

<pre><div node="[object Object]" class="relative whitespace-pre-wrap word-break-all my-2 rounded-xl bg-muted border"><div class="min-h-7 relative box-border flex flex-row items-center justify-between rounded-t border-b border-border px-2 py-0.5"><div class="font-sans text-sm text-muted-foreground">powershell</div><div class="flex flex-row gap-2 justify-end"></div></div><div class="p-3"><div class="w-full h-full text-xs cursor-text"><div class="code-block"><div class="code-line" data-line-number="1" data-line-start="1" data-line-end="1"><div class="line-content"><span class="mtk10">$env:PYTHONPATH</span><span class="mtk3">=</span><span class="mtk12">"."</span><span class="mtk1"> ; python tests</span><span class="mtk3">/</span><span class="mtk1">test_unhinged.py</span></div></div></div></div></div></div></pre>

---

### 4. ⚡ Quick Single-Query Verification

Executes a single test query ( *"What is Article 21?"* ) inside the generator module class entrypoint.

**How to run:**

<pre><div node="[object Object]" class="relative whitespace-pre-wrap word-break-all my-2 rounded-xl bg-muted border"><div class="min-h-7 relative box-border flex flex-row items-center justify-between rounded-t border-b border-border px-2 py-0.5"><div class="font-sans text-sm text-muted-foreground">powershell</div><div class="flex flex-row gap-2 justify-end"></div></div><div class="p-3"><div class="w-full h-full text-xs cursor-text"><div class="code-block"><div class="code-line" data-line-number="1" data-line-start="1" data-line-end="1"><div class="line-content"><span class="mtk10">$env:PYTHONPATH</span><span class="mtk3">=</span><span class="mtk12">"."</span><span class="mtk1"> ; python src</span><span class="mtk3">/</span><span class="mtk1">retrieval</span><span class="mtk3">/</span><span class="mtk1">generator.py</span></div></div></div></div></div></div></pre>
