let nodesData = [];
let edgesData = [];
let nodeMap = new Map();
let visNetwork = null;
let visNodes = null;
let visEdges = null;
const API_URL = "http://127.0.0.1:8000";

async function initGraph() {
    let data;
    try {
        const response = await fetch(`${API_URL}/graph`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        data = await response.json();
    } catch (err) {
        console.warn('Failed to fetch from server, falling back to local JSON:', err);
    }

    if (!data || !Array.isArray(data)) {
        try {
            const localRes = await fetch('kg/knowledge_graph.json');
            data = await localRes.json();
            console.log('Loaded graph from local JSON');
        } catch (localErr) {
            console.error('Failed to load local JSON as well:', localErr);
            return;
        }
    }

    // Build node map to deduplicate and assign unique IDs
    const rawNodes = data.filter(item => item.type === 'node');
    const rawEdges = data.filter(item => item.type === 'edge');

    // Deduplicate nodes by name; keep first occurrence, append suffix for duplicates
    let nameCount = {};
    rawNodes.forEach(n => {
        const baseName = n.name;
        if (nameCount[baseName] === undefined) {
            nameCount[baseName] = 0;
        }
        nameCount[baseName]++;
        const uniqueId = nameCount[baseName] > 1 ? `${baseName}__${nameCount[baseName]}` : baseName;
        nodeMap.set(baseName + '__' + (nameCount[baseName]), { ...n, _uniqueId: uniqueId });
        // Also map the first occurrence
        if (nameCount[baseName] === 1) {
            nodeMap.set(baseName + '__1', { ...n, _uniqueId: uniqueId });
        }
    });

    // Collect all nodes with their unique IDs
    nodesData = [];
    rawNodes.forEach((n, idx) => {
        const baseName = n.name;
        // Track per-name occurrences
        if (!nameCount[`_seen_${baseName}`]) nameCount[`_seen_${baseName}`] = 0;
        nameCount[`_seen_${baseName}`]++;
        const count = nameCount[`_seen_${baseName}`];
        const uniqueId = count > 1 ? `${baseName}__${count}` : baseName;
        nodesData.push({ ...n, _uniqueId: uniqueId });
    });

    // Reset counter for edges lookup
    let nodeNameCounter = {};
    rawNodes.forEach(n => {
        if (!nodeNameCounter[n.name]) nodeNameCounter[n.name] = 0;
        nodeNameCounter[n.name]++;
    });

    // Build a lookup: (nodeName, occurrenceIndex) -> uniqueId
    let occurrenceIndex = {};
    const nodeIdLookup = {}; // nodeName -> array of uniqueIds in order
    rawNodes.forEach(n => {
        if (!nodeIdLookup[n.name]) nodeIdLookup[n.name] = [];
        const uniqueId = nodeIdLookup[n.name].length > 0
            ? `${n.name}__${nodeIdLookup[n.name].length + 1}`
            : n.name;
        nodeIdLookup[n.name].push(uniqueId);
    });

    // Process edges: resolve from/to to valid unique IDs
    edgesData = rawEdges.map(e => ({
        ...e,
        _from: nodeIdLookup[e.from] ? nodeIdLookup[e.from][0] : e.from,
        _to: nodeIdLookup[e.to] ? nodeIdLookup[e.to][0] : e.to
    })).filter(e => {
        // Filter out edges that reference non-existent nodes
        if (!nodeIdLookup[e.from] || !nodeIdLookup[e.to]) {
            console.warn(`Skipping edge "${e.name}": missing node(s): from=${e.from}, to=${e.to}`);
            return false;
        }
        return true;
    });

    console.log(`Graph loaded: ${nodesData.length} nodes, ${edgesData.length} edges`);
    renderGraph();
}

function renderGraph() {
    visNodes = new vis.DataSet(nodesData.map(n => ({
        id: n._uniqueId,
        label: n.label || n.name,
        color: {
            background: n.color,
            border: n.color,
            highlight: { background: n.color, border: '#1a73e8' }
        },
        shape: 'dot',
        size: (n.name === "EverMemOS" || n.name === "MAGMA" || n.name === "CompassMem") ? 35 : 20,
        font: { size: 14, color: '#3c4043', face: 'Google Sans' },
        margin: 10
    })));

    visEdges = new vis.DataSet(edgesData.map((e, index) => ({
        id: 'e' + index,
        from: e._from,
        to: e._to,
        label: e.label || e.name,
        arrows: 'to',
        font: { align: 'middle', size: 11, color: '#70757a' },
        color: { color: '#dadce0', highlight: '#4285f4' },
        width: 1.5
    })));

    const container = document.getElementById('mynetwork');
    const options = {
        physics: {
            enabled: true,
            stabilization: { iterations: 150, fit: true },
            barnesHut: { gravitationalConstant: -2000, springLength: 150, springConstant: 0.05 }
        },
        interaction: { hover: true, tooltipDelay: 200, navigationButtons: true, keyboard: true },
        layout: { improvedLayout: true }
    };

    visNetwork = new vis.Network(container, { nodes: visNodes, edges: visEdges }, options);

    visNetwork.on("click", function (params) {
        if (params.nodes.length > 0) {
            const nodeInfo = nodesData.find(n => n._uniqueId === params.nodes[0]);
            if (nodeInfo) {
                showDetails(nodeInfo.label || nodeInfo.name, nodeInfo.content);
            }
        } else {
            hideDetails();
        }
    });

    // Bind search input
    document.getElementById('search-input').addEventListener('input', debounce(function (e) {
        filterGraph(e.target.value.trim());
    }, 300));
}

initGraph();

function showDetails(title, content) {
    const win = document.getElementById('details-window');
    document.getElementById('info-title').innerText = title;
    document.getElementById('info-content').innerText = content;
    win.style.display = 'block';
}

function hideDetails() {
    document.getElementById('details-window').style.display = 'none';
}

function debounce(fn, delay) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

function jaro(s1, s2) {
    if (s1 === s2) return 1.0;
    const len1 = s1.length, len2 = s2.length;
    if (len1 === 0 || len2 === 0) return 0.0;
    const matchDist = Math.floor(Math.max(len1, len2) / 2) - 1;
    const matches = new Array(Math.max(len1, len2)).fill(false);
    let m = 0;

    for (let i = 0; i < len1; i++) {
        const lo = Math.max(0, i - matchDist), hi = Math.min(len2, i + matchDist + 1);
        for (let j = lo; j < hi; j++) {
            if (matches[j] || s1[i] !== s2[j]) continue;
            matches[j] = true; m++; break;
        }
    }

    if (m === 0) return 0.0;
    let t = 0, k = 0;
    for (let i = 0; i < len1; i++) {
        if (!matches[i]) continue;
        while (!matches[k]) k++;
        if (s1[i] !== s2[k]) t++;
        k++;
    }
    return (m / len1 + m / len2 + (m - t / 2) / m) / 3;
}

function similarity(a, b) {
    a = a.toLowerCase(); b = b.toLowerCase();
    const dist = jaro(a, b);
    const p = 0.1;
    let l = 0;
    while (l < Math.min(4, Math.min(a.length, b.length)) && a[l] === b[l]) l++;
    return dist + l * p * (1 - dist);
}

function filterGraph(keyword) {
    if (!visNodes || !visEdges || !visNetwork) return;

    if (!keyword) {
        visNodes.clear();
        visEdges.clear();
        visNodes.add(nodesData.map(n => ({
            id: n._uniqueId,
            label: n.label || n.name,
            color: { background: n.color, border: n.color, highlight: { background: n.color, border: '#1a73e8' } },
            shape: 'dot',
            size: (n.name === "EverMemOS" || n.name === "MAGMA" || n.name === "CompassMem") ? 35 : 20,
            font: { size: 14, color: '#3c4043', face: 'Google Sans' },
            margin: 10
        })));
        visEdges.add(edgesData.map((e, index) => ({
            id: 'e' + index, from: e._from, to: e._to,
            label: e.label || e.name, arrows: 'to',
            font: { align: 'middle', size: 11, color: '#70757a' },
            color: { color: '#dadce0', highlight: '#4285f4' }, width: 1.5
        })));
        visNetwork.fit();
        return;
    }

    const THRESHOLD = 0.7;
    const matchedNodeIds = new Set();

    nodesData.forEach(n => {
        const labelScore = similarity(keyword, n.label || n.name);
        const nameScore = similarity(keyword, n.name);
        const score = Math.max(labelScore, nameScore);
        if (score >= THRESHOLD) {
            matchedNodeIds.add(n._uniqueId);
        }
    });

    const filteredNodeSet = new Set(matchedNodeIds);
    edgesData.forEach(e => {
        if (matchedNodeIds.has(e._from) && matchedNodeIds.has(e._to)) {
            // keep edge
        }
    });

    visNodes.clear();
    visEdges.clear();

    const filteredNodes = nodesData.filter(n => filteredNodeSet.has(n._uniqueId));
    const filteredEdgeIds = new Set(filteredNodes.map(n => n._uniqueId));

    visNodes.add(filteredNodes.map(n => ({
        id: n._uniqueId,
        label: n.label || n.name,
        color: { background: n.color, border: n.color, highlight: { background: n.color, border: '#1a73e8' } },
        shape: 'dot',
        size: (n.name === "EverMemOS" || n.name === "MAGMA" || n.name === "CompassMem") ? 35 : 20,
        font: { size: 14, color: '#3c4043', face: 'Google Sans' },
        margin: 10
    })));

    visEdges.add(edgesData.map((e, index) => ({
        id: 'e' + index, from: e._from, to: e._to,
        label: e.label || e.name, arrows: 'to',
        font: { align: 'middle', size: 11, color: '#70757a' },
        color: { color: '#dadce0', highlight: '#4285f4' }, width: 1.5
    })).filter(e => filteredEdgeIds.has(e.from) && filteredEdgeIds.has(e.to)));

    if (filteredNodes.length > 0) {
        visNetwork.fit({ animation: { duration: 300, easingFunction: 'easeInOutQuad' } });
    }
}
