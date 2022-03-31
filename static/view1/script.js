function scaleAttribute(data, attribute, min, max) {
    data = data.map(d => {
        d[attribute] = min + d[attribute] * (max - min);
        return d;
    });
    return data;
}

function boundNodes(nodes) {
    const constrainBox = { x: 10, y: 10, width: width, height: height };
    let minx = 99999999;
    let maxx = -99999999;
    let miny = 99999999;
    let maxy = -99999999;
    let maxsize = -9999999;
    nodes.forEach((node) => {
        if (minx > node.x) {
            minx = node.x;
        }
        if (maxx < node.x) {
            maxx = node.x;
        }
        if (miny > node.y) {
            miny = node.y;
        }
        if (maxy < node.y) {
            maxy = node.y;
        }
        if (maxsize < node.size) {
            maxsize = node.size;
        }
    });
    const scalex = (constrainBox.width - maxsize) / (maxx - minx);
    const scaley = (constrainBox.height - maxsize) / (maxy - miny);
    nodes.forEach((node) => {
        node.x = (node.x - minx) * scalex + constrainBox.x;
        node.y = (node.y - miny) * scaley + constrainBox.y;
    });
}

function scaleData(data, nodeMin, nodeMax, edgeMin, edgeMax) {
    data.nodes = scaleAttribute(data.nodes, 'size', nodeMin, nodeMax);
    data.edges = scaleAttribute(data.edges, 'weight', edgeMin, edgeMax);
    return data;
}

function preprocessData(data) {
    let l1_data = data.level1;
    let l2_data = data.level2;

    l1_data = scaleData(l1_data, 30, 50, 800, 1200);
    l2_data = scaleData(l2_data, 20, 100, 800, 1200);

    return [l1_data, l2_data]
}

function createMainGraph(data, width, height) {
    nodes = data.nodes;
    mainGraph = new G6.Graph({
        container: mainContainer,
        width,
        height,
        modes: {
            default: ['drag-canvas', 'zoom-canvas', 'activate-relations', 'drag-node']
        },
        animate: true,
        animateCfg: {
            duration: 500, // Number, the duration of one animation
            // easing: 'easePolyIn', // String, the easing function
        },

        layout: {
            type: 'gForce',
            center: [700, 500],
            edgeStrength: (e) => { return e.weight; },
            nodeStrength: (n) => { return n.size + 200; },
            linkDistance: 50,
            workerEnabled: true, // Whether to activate web-worker
        },

        nodeStateStyles: {
            selected: {
                stroke: '#7509bd',
                lineWidth: 3,
            }
        }
    });

    mainGraph.data({
        nodes: nodes,
        edges: data.edges.map(function (edge, i) {
            edge.id = 'edge' + i;
            return Object.assign({}, edge);
        }),
    });

    mainGraph.render();

    mainGraph.on('node:click', (e) => {

        // clear previous selected nodes if equal to 2
        let nodes = mainGraph.findAllByState('node', 'selected');
        if(nodes.length == 2) {
            nodes.forEach(n => {
                mainGraph.clearItemStates(n, 'selected');
            })
        }


        let node = e.item;
        if(node.hasState('selected'))
        {
            mainGraph.setItemState(e.item, 'selected', false);
        } else {
            mainGraph.setItemState(e.item, 'selected', true);
        }
        
        getPapers();

    });

    if (typeof window !== 'undefined')
        window.onresize = () => {
            if (!mainGraph || mainGraph.get('destroyed')) return;
            if (!mainGraph || !mainGraph.scrollWidth || !mainGraph.scrollHeight) return;
            mainGraph.changeSize(mainGraph.scrollWidth, mainGraph.scrollHeight);
        };
}

function createSubGraph(data, width, height) {
    nodes = data.nodes;
    subGraph = new G6.Graph({
        container: subContainer,
        width,
        height,
        modes: {
            default: ['drag-canvas', 'zoom-canvas', 'activate-relations', 'drag-node']
        },
        animate: true,
        animateCfg: {
            duration: 500, // Number, the duration of one animation
            // easing: 'easePolyIn', // String, the easing function
        },

        layout: {
            type: 'concentric',
            center: [width / 2, height / 2],
            nodeSize: 50,
            preventOverlap: true,
            workerEnabled: true, // Whether to activate web-worker
        }
    });

    subGraph.data({
        nodes: nodes,
        edges: data.edges.map(function (edge, i) {
            edge.id = 'edge' + i;
            return Object.assign({}, edge);
        }),
    });

    subGraph.render();

    if (typeof window !== 'undefined')
        window.onresize = () => {
            if (!subGraph || subGraph.get('destroyed')) return;
            if (!subGraph || !subGraph.scrollWidth || !subGraph.scrollHeight) return;
            subGraph.changeSize(subGraph.scrollWidth, subGraph.scrollHeight);
        };
}

function nextFrame() {
    return fetch('http://127.0.0.1:5000/view1/data/' + (currFrameNumber + 1))
        .then((res) => res.json())
        .then((data) => preprocessData(data))
        .then((data) => {
            let l1_data = data[0];
            let l2_data = data[1];
            mainGraph.changeData(l2_data);
            subGraph.changeData(l1_data);
            $('#papers').empty();
        })
        .then(() => currFrameNumber = currFrameNumber + 1) 
}

function prevFrame() {
    return fetch('http://127.0.0.1:5000/view1/data/' + (currFrameNumber - 1))
        .then((res) => res.json())
        .then((data) => preprocessData(data))
        .then((data) => {
            let l1_data = data[0];
            let l2_data = data[1];
            mainGraph.changeData(l2_data);
            subGraph.changeData(l1_data);
            $('#papers').empty();
        })
        .then(() => currFrameNumber = currFrameNumber - 1) 
}


function getPapers() {
    let concepts = mainGraph.findAllByState('node', 'selected').map(x => x._cfg.model.cid);
    $('#papers').empty();
    // console.log(concepts.length);
    if(concepts.length == 2) {
        let cid1 = concepts[0];
        let cid2 = concepts[1];

        console.log(concepts);

        // url = 'http://127.0.0.1:5000/papers?cid1=' + cid1 + '&' + 'cid2=' + cid2 + '&' + 'frame_number=' + currFrameNumber;
        let url = `http://127.0.0.1:5000/view1/papers?cid1=${cid1}&cid2=${cid2}&frame_number=${currFrameNumber}`;
        fetch(url)
            .then(res => res.json())
            .then(res => {
                let papers = res.papers;
                console.log(papers);
                
                papers.forEach(p => {
                    let link = document.createElement('a');
                    link.innerHTML = p.name;
                    link.setAttribute('class', 'list-group-item');
                    link.setAttribute('href', p.link);
                    link.setAttribute('target', '_blank');
                    link.setAttribute('ref', 'noopener noreferrer');

                    let listItem = document.createElement('li');
                    listItem.appendChild(link);
                    $('#papers').append(listItem);
                });
            })
    }
}