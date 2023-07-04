import React, { Component, useEffect } from "react";
import ForceGraph3D from "react-force-graph-3d";
import ForceGraph2D from "react-force-graph-2d";
import GraphData from "../../../../../data/oeo_viewer_json_data.json";
import SpriteText from "three-spritetext";
import CustomDialog from "../presentational/customDialog";
import CustomMenu from "../presentational/customMenu";
import BaseCard from "../presentational/baseCard";
import CustomCard from "../presentational/customCard";
import CustomSubmitButton from "../presentational/customSubmitButton";
import CustomTreeView from "./customTreeView";
import LayoutActions from "./actions.js";
import Grid from "@material-ui/core/Grid";

import * as d3 from 'd3';

class Layout extends Component {
  constructor(props) {
    super(props);
    this.fgRef = React.createRef();
    this.updateWindowDimensions = this.updateWindowDimensions.bind(this);
    this.prepareData = this.prepareData.bind(this);
    this.focusHandler = this.focusHandler.bind(this);
    this.fitAllHandler = this.fitAllHandler.bind(this);
    this.annotateDatabaseHandler = this.annotateDatabaseHandler.bind(this);
    this.shrinkHandler = this.shrinkHandler.bind(this);
    this.expandHandler = this.expandHandler.bind(this);
    this.viewAllHandler = this.viewAllHandler.bind(this);
    this.treeViewSelectHandler = this.treeViewSelectHandler.bind(this);
    this.showParentHandler = this.showParentHandler.bind(this);
    this.HierarchicalViewHandler = this.HierarchicalViewHandler.bind(this);
    this.searchHandler = this.searchHandler.bind(this);
    // this.filterGraph = this.filterGraph.bind(this);
    // this.traverseTree = this.traverseTree.bind(this);
  }

  state = {
    openSettingDialog: false,
    currentNode: "",
    hierarchicalView: true,
    cooldownTicks: 1000
  };

  componentWillMount() {
    this.prepareData();
    this.searchHandler("OEO_00000150");
  }

  componentDidMount() {
    this.updateWindowDimensions();
    window.addEventListener('resize', this.updateWindowDimensions);
    this.fgRef.current.d3Force("center", d3.forceCenter(50, 50));
    this.fgRef.current.d3Force("collide", d3.forceCollide().radius(30));
    this.fgRef.current.d3Force("charge").strength(-40);
    this.fgRef.current.d3Force("charge", d3.forceManyBody().strength(-2))
    //this.fgRef.current.d3Force("link").distance(link => link.value);
    //this.fgRef.current.d3Force("link").distance(40);
    //this.fgRef.current.d3Force('collision', d3.forceCollide(100));
    //this.fgRef.current.d3Force('link', d3.forceLink().distance(100));
    //this.fgRef.current.d3Force('charge', d3.forceManyBody().theta(0.1).strength(-1));
    //this.fgRef.current.d3Force("collision").forceCollide(node => Math.sqrt(100 / (node.level + 1)));
    //fgRef.current.d3Force('collision', d3.forceCollide(node => Math.sqrt(100 / (node.level + 1))));
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.updateWindowDimensions);
  }

  updateWindowDimensions() {
  this.setState({
    width: window.innerWidth / 1.23 ,
    height: window.innerHeight / 1.8
  });
  }

  handleSettingDialogOpen = status => {
    this.setState({ openSettingDialog: true });
  };

  handleSettingDialogClose = status => {
    this.setState({ openSettingDialog: false });
  };

  handleNodeRightClick = node => {
    this.setState({
      openSettingDialog: true,
      currentNode: node
    });
  };

  handleNodeClick = node => {
    const allLinks = GraphData.links;
    let treeData = [];

    allLinks.forEach(link => {
        if ((typeof link.source) === 'object') {
          treeData.push({'id': link.target.id, 'parent': link.source.id});
        }
        else {
          treeData.push({'id': link.target, 'parent': link.source});
        }
    });
    const currentNode = treeData.find(link => link.id === node.id);
    let allParents = [];

    if(currentNode !== undefined) {
      (function traverseTreeBack(node = currentNode) {
          allParents.unshift(node.id);
          if (node.id == 'BFO_0000001' || node.parent == 'BFO_0000001') return;
          const parentNode = treeData.find(link => link.id === node.parent);
          traverseTreeBack(parentNode);
        })();
    };

    allParents.unshift('BFO_0000001');
    this.setState({
      currentNode: node,
      currentNodeAllParents: allParents,
      cooldownTicks: 5,
    });
  };

  focusHandler() {
    this.fgRef.current.centerAt(
      this.state.currentNode.x,
      this.state.currentNode.y,
      100
    );
    this.fgRef.current.zoom(5, 300);
  };

  fitAllHandler() {
    this.fgRef.current.zoomToFit(200, 150);
  };

  annotateDatabaseHandler() {
    this.setState({
      openSettingDialog: true,
    });
  };

  expandHandler() {
    const allNodes = GraphData.nodes;
    const allLinks = GraphData.links;
    const visibleLinks = this.state.ontologyData.links;
    const visibleNodes = this.state.ontologyData.nodes;
    const currentNode = this.state.currentNode;

    allLinks.forEach(link => {
      if ((typeof link.source) === 'object') {
        if (link.source.id === currentNode.id) {
          const linkExist = visibleLinks.find(l => (l.source.id === link.source.id && l.target.id === link.target.id)) !== undefined;
          if (!linkExist) {
            visibleLinks.push(link);
            const currentNodeChild = allNodes.find(node => node.id === link.target.id);
            visibleNodes.push(currentNodeChild);
          }
        }
      }
      else {
        if (link.source === currentNode.id) {
          const linkExist = visibleLinks.find(l => (l.id === link.source)) !== undefined;
          if (!linkExist) {
            visibleLinks.push(link);
            const currentNodeChild = allNodes.find(node => node.id === link.target);
            visibleNodes.push(currentNodeChild);
          }
        }
      }
    });

    this.setState({
      ontologyData: {
        'nodes': visibleNodes,
        'links': visibleLinks
      }
    });
  };

  showParentHandler() {
    const allNodes = GraphData.nodes;
    const allLinks = GraphData.links;
    const visibleLinks = this.state.ontologyData.links;
    const visibleNodes = this.state.ontologyData.nodes;
    const currentNode = this.state.currentNode;


    allLinks.forEach(link => {
      if ((typeof link.target) === 'object') {
        if (link.target.id === currentNode.id) {
          const linkExist = visibleLinks.find(l => (l.source.id === link.source.id && l.target.id === link.target.id)) !== undefined;
          if (!linkExist) {
            visibleLinks.push(link);
            const currentNodeParent = allNodes.find(node => node.id === link.source.id);
            visibleNodes.push(currentNodeParent);
          }
        }
      }
      else {
        if (link.target === currentNode.id) {
          const linkExist = visibleLinks.find(l => (l.id === link.source)) !== undefined;
          if (!linkExist) {
            visibleLinks.push(link);
            const currentNodeParent = allNodes.find(node => node.id === link.source);
            visibleNodes.push(currentNodeParent);
          }
        }
      }
    });
    this.setState({
      ontologyData: {
        'nodes': visibleNodes,
        'links': visibleLinks
      }
    });
  };

  viewAllHandler() {
    this.setState({
      ontologyData: GraphData
    }, () => {
      this.fgRef.current.zoomToFit(200, 150);
    });
  };

  searchHandler(nodeId) {
    const allLinks = GraphData.links;
    const allNodes = GraphData.nodes;
    const searchedtNode = allNodes.find(node => node.id === nodeId);
    const filteredNodes = [searchedtNode];
    const filteredLinks = [];

    allLinks.forEach(link => {
      if ((typeof link.source) === 'object') {
        if (link.source.id === searchedtNode.id) {
          filteredLinks.push(link);
          const searchedtNodeChild = allNodes.find(node => node.id === link.target.id);
          filteredNodes.push(searchedtNodeChild);
        }
      }
      else {
        if (link.source === searchedtNode.id) {
          filteredLinks.push(link);
          const searchedtNodeChild = allNodes.find(node => node.id === link.target);
          filteredNodes.push(searchedtNodeChild);
        }
      }
    });

    let treeData = [];
    allLinks.forEach(link => {
        if ((typeof link.source) === 'object') {
          treeData.push({'id': link.target.id, 'parent': link.source.id});
        }
        else {
          treeData.push({'id': link.target, 'parent': link.source});
        }
    });

    let allParents = [];
    const searchedNodeInTreeData = treeData.find(link => link.id === searchedtNode.id);

    (function traverseTreeBack(node = searchedNodeInTreeData) {
        allParents.unshift(node.id);
        if (node.id === 'BFO_0000001' || node.parent === 'BFO_0000001') return;
        const parentNode = treeData.find(link => link.id === node.parent);
        traverseTreeBack(parentNode);
      })();

    allParents.unshift('BFO_0000001');

    this.setState({
      ontologyData: {
        'links': filteredLinks,
        'nodes': filteredNodes
      }
    }, () => {
      this.setState({
        currentNode: searchedtNode,
        currentNodeAllParents: allParents
      });
    });

  };

  HierarchicalViewHandler() {
    this.setState({
      hierarchicalView: !this.state.hierarchicalView
    }, () => {
      this.fgRef.current.zoomToFit(200, 200);
    });
  };

  prepareData() {
    const allLinks = GraphData.links;
    const allNodes = GraphData.nodes;

    const classIDFromURL = window.location.href.split('/').pop();
    const requestedNode = allNodes.find(node => node.id === classIDFromURL);

    let treeData = [];
    allLinks.forEach(link => {
      const targetName = allNodes.find(node => node.id === link.target);
      const sourceName = allNodes.find(node => node.id === link.source);
      if (sourceName !== undefined && targetName !== undefined)
         treeData.push({'id': link.target,
                        'parent': link.source,
                        'name': targetName['name'],
                        'parent_parent': sourceName['name']}
                      );
      }
    );

    function findFor(parentId) {
      var z = [];
      for (var i = 0; i < treeData.length; i++){
        if (treeData[i].parent === parentId) {
          var ch = findFor(treeData[i].id);
          var o = Object.keys(ch).length === 0 ? {} : { children: ch };
          z.push(Object.assign(o, treeData[i]));
        }
      }
      return z;
    }

    const rootChildren = findFor("BFO_0000001");

    const treeViewData = {
      id: 'BFO_0000001',
      name: 'Entity',
      children: rootChildren
    }

    const rootNode = allNodes.find(node => node.id === 'BFO_0000001');
    const nodeToStart =  requestedNode !== undefined ? requestedNode :rootNode
    const filteredNodes = [nodeToStart];
    const filteredLinks = [];

    allLinks.forEach(link => {
      if ((typeof link.source) === 'object') {
        if (link.source.id === nodeToStart.id) {
          filteredLinks.push(link);
          const nodeToStartChild = allNodes.find(node => node.id === link.target.id);
          filteredNodes.push(nodeToStartChild);
        }
      }
      else {
        if (link.source === nodeToStart.id) {
          filteredLinks.push(link);
          const nodeToStartChild = allNodes.find(node => node.id === link.target);
          filteredNodes.push(nodeToStartChild);
        }
      }
    });

    let allParents = [];
    if (requestedNode !== undefined) {
      const searchedNodeInTreeData = treeData.find(link => link.id === requestedNode.id);
      (function traverseTreeBack(node = searchedNodeInTreeData) {
          allParents.unshift(node.id);
          if (node.id === 'BFO_0000001' || node.parent === 'BFO_0000001') return;
          const parentNode = treeData.find(link => link.id === node.parent);
          traverseTreeBack(parentNode);
        })();

      allParents.unshift('BFO_0000001');
    }


    this.setState({
      treeViewData: treeViewData,
      currentNodeAllParents: requestedNode !== undefined ? allParents : ['Entity'],
      currentNode: nodeToStart,
      ontologyData: {
        'links': filteredLinks,
        'nodes': filteredNodes
      }
    });
    };


  shrinkHandler() {
    const allNodes = this.state.ontologyData.nodes;
    const allLinks = this.state.ontologyData.links;
    const currentNode = this.state.currentNode;
    const nodesById = Object.fromEntries(allNodes.map(node => [node.id, node]));

    const filteredLinks = [];
    const filteredNodes = [];
    let visibleNodes = [];
    let visibleLinks = [];

    const allNodeIds = allNodes.map(n => n.id);
    const allLinkTargets = allLinks.map(l => (typeof l.target) === 'object' ? l.target.id : l.target);
    const topMostNodeId = allNodeIds.filter(x => !allLinkTargets.includes(x));


    allNodes.forEach(node => {
      node.childLinks = [];
    });

    allLinks.forEach(link => {
      if ((typeof link.target) === 'object') {
        nodesById[link.source.id].childLinks.push(link);
        if (link.source.id === currentNode.id) {
          filteredLinks.push(link);
          filteredNodes.push(link.target);
        }
      }
      else {
        nodesById[link.source].childLinks.push(link);
        if (link.source === currentNode.id) {
          filteredLinks.push(link);
          const currentNode = allNodes.find(node => node.id === link.target);
          visibleNodes.push(currentNodeParent);
        }
      }
    });

    let traversedLinks = [];

    (function traverseTree(node = nodesById[topMostNodeId]) {
        const nodeFound = filteredNodes.find(el => el.id === node.id) !== undefined;
        if (nodeFound) return;
        visibleNodes.push(node);
        traversedLinks.push(...node.childLinks);

        node.childLinks
          .map(link => ((typeof link.target) === 'object') ? link.target : nodesById[link.target])
          .forEach(traverseTree);
      })();

    visibleLinks = traversedLinks.filter(el => filteredNodes.find(n => n.id === el.target.id) === undefined);

    this.setState({
      ontologyData: {
        'nodes': visibleNodes,
        'links': visibleLinks
      }
    });

  };

  treeViewSelectHandler(event, nodeId) {
    const allNodes = GraphData.nodes;
    const allLinks = GraphData.links;

    const selectedNode = allNodes.find(node => node.id === nodeId);

    const filteredNodes = [selectedNode];
    const filteredLinks = [];

    allLinks.forEach(link => {
      if ((typeof link.source) === 'object') {
        if (link.source.id === selectedNode.id) {
          filteredLinks.push(link);
          const rootNodeChild = allNodes.find(node => node.id === link.target.id);
          filteredNodes.push(rootNodeChild);
        }
      }
      else {
        if (link.source === selectedNode.id) {
          filteredLinks.push(link);
          const rootNodeChild = allNodes.find(node => node.id === link.target);
          filteredNodes.push(rootNodeChild);
        }
      }
    });

    this.setState({
      currentNode: selectedNode,
      ontologyData: {
        'links': filteredLinks,
        'nodes': filteredNodes
      }
    });
  }


  renderSense() {
    return (
            <ForceGraph2D
              height={this.state.height}
              width={this.state.width}
              graphData={this.state.ontologyData}
              backgroundColor={"#f7f7f7"}
              nodeOpacity={1}
              showNavInfo={false}
              nodeResolution={20}
              //nodeAutoColorBy="group"
              //nodeAutoColorBy={node => node.current !== undefined ? "#ff0000": "#f7f7f7"}
              // nodeCanvasObject={(node, ctx, globalScale) => {
              //   const label = node.name;
              //   const fontSize = 12 / globalScale;
              //   ctx.font = `Bold ${fontSize}px Tahoma`;
              //   const textWidth = ctx.measureText(label).width;
              //   const bckgDimensions = [textWidth, fontSize].map(
              //     n => n + fontSize * 1.2
              //   ); // some padding
              //
              //   ctx.fillStyle = node.id === this.state.currentNode.id ? "#009688" :'#deeaee';
              //   ctx.fillRect(
              //     node.x - bckgDimensions[0] / 2,
              //     node.y - bckgDimensions[1] / 2,
              //     ...bckgDimensions
              //   );
              //
              //   ctx.lineWidth = 0.05;
              //   ctx.strokeRect(
              //     node.x - bckgDimensions[0] / 2,
              //     node.y - bckgDimensions[1] / 2,
              //     ...bckgDimensions
              //   );
              //
              //   ctx.textAlign = "center";
              //   ctx.textBaseline = "middle";
              //   ctx.fillStyle = node.id === this.state.currentNode.id ? "#ffffff" : "#034f84";
              //   ctx.strokeStyle = "#00688B";
              //   ctx.fillText(label, node.x, node.y);
              //
              //   node.__bckgDimensions = bckgDimensions; // to re-use in nodePointerAreaPaint
              // }}

              nodeCanvasObject={(node, ctx, globalScale) => {
                    
                    //ctx.fillStyle = node.id === this.state.currentNode.id ? "#009688" :'#deeaee';

                    /* ctx.beginPath();
                    ctx.arc(node.x, node.y, 12, 0, 2 * Math.PI);
                    ctx.stroke();
                    ctx.fill();

                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillStyle =  node.id === this.state.currentNode.id ? "#ffffff" :'#034f84';
                    ctx.strokeStyle = "#00688B";
                    ctx.lineWidth = 2; */

                    const label = node.name;
                    var num_of_words = label.split(" ").length;

                    ctx.fillStyle =  node.id === this.state.currentNode.id ? "#78C1AE" :'#04678F';
                    ctx.fillRect(node.x - 2, node.y - 5, 18 * num_of_words, 8); 

                    const fontSize = 3;
                    ctx.font = `${fontSize}px Tahoma`;
                    ctx.fillStyle = node.id === this.state.currentNode.id ? "#04678F" :'#ffffff';
                    ctx.fillText(label, node.x, node.y )
                    
                    

                    /* if (lines.length == 1) {
                      ctx.fillText(lines[0], node.x, node.y )
                    } else {
                      for (var i = 0; i<lines.length; i++) {
                        if (i == 0) {
                          ctx.fillText(lines[i], node.x, node.y - 8 );
                        } else if (i == 1) {
                          ctx.fillText(lines[i], node.x, node.y - 2 );
                        } else if (i == 2) {
                          ctx.fillText(lines[i], node.x, node.y + 4 );
                        } else {
                          ctx.fillText(lines[i], node.x, node.y + 10 );
                        }
                      }
                    } */


                    const textWidth = ctx.measureText(label).width;
                    const bckgDimensions = [textWidth, fontSize].map(
                      n => n + fontSize * 6
                      ); // some padding
                      node.__bckgDimensions = bckgDimensions; // to re-use in nodePointerAreaPaint
                    }}

              nodePointerAreaPaint={(node, color, ctx) => {
                ctx.fillStyle = color;
                const bckgDimensions = node.__bckgDimensions;
                bckgDimensions &&
                  ctx.fillRect(
                    node.x - bckgDimensions[0] / 2,
                    node.y - bckgDimensions[1] / 2,
                    ...bckgDimensions
                  );
              }}
              ref={this.fgRef}
              //onNodeRightClick={n => {
              //  this.handleNodeRightClick(n);
              //}}
              linkDirectionalArrowLength={5}
              linkDirectionalArrowRelPos={0.5}
              //linkCurvature={0.25}
              dagMode={this.state.hierarchicalView ? "td" : ""}
              linkColor={() => "#9AC0CD"}
              d3VelocityDecay={0.01}
              dagLevelDistance={50}
              // d3VelocityDecay={0.001}
              // dagLevelDistance={200}
              cooldownTicks={this.state.cooldownTicks}
              cooldownTime={1000}
              onNodeDragEnd={node => {
                node.fx = node.x;
                node.fy = node.y;
                node.fz = node.z;
              }}
              onNodeClick={n => {
                this.handleNodeClick(n);
              }}
            />
    );
  }

  render() {
      return (
        <div>
        <Grid
          container
          direction="row"
          justifyContent="center"
          //alignItems="stretch"
          spacing={2}>
              <Grid item xs={3}>
                  <CustomTreeView
                    treeViewData={this.state.treeViewData}
                    expanded={this.state.currentNodeAllParents}
                    treeViewSelectHandler={this.treeViewSelectHandler}
                    />
                 {/*  <div style={{ padding: "15px" }}>
                  If you find bugs or if you have ideas to improve the Open Energy Platform, you are welcome to add your comments to the existing issues on
                  <a href="https://github.com/OpenEnergyPlatform/oeplatform"> GitHub. </a>
                  </div>

                  <div style={{ padding: "15px" }}>
                  You can also fork the project and get involved.
                  Please note that the platform is still under construction and therefore the design of this page is still highly volatile!
                  </div> */}
              </Grid>
              <Grid item xs={9} >
                <Grid
                  container
                  direction="column"
                  justifyContent="center"
                >
                {<CustomCard
                  nodeInfo={this.state.currentNode}
                />}

                <div style={{ "padding": "15px 0px 0px 0px", "height": "60px" }}>
                  {<LayoutActions
                    annotate={false}
                    viewAll={true}
                    search={true}
                    hierarchicalView={true}
                    focusHandler={this.focusHandler}
                    fitAllHandler={this.fitAllHandler}
                    annotateDatabaseHandler={this.annotateDatabaseHandler}
                    expandHandler={this.expandHandler}
                    showParentHandler={this.showParentHandler}
                    shrinkHandler={this.shrinkHandler}
                    viewAllHandler={this.viewAllHandler}
                    toggleRenderMode={this.toggleRenderMode}
                    HierarchicalViewHandler={this.HierarchicalViewHandler}
                    searchHandler={this.searchHandler}
                    />}
                 </div>
                 <div style={{
                     "borderStyle": "solid",
                     "borderWidth": "1px",
                     "backgroundColor": "#f7f7f7",
                     "borderColor": "#00688B" }}>
                  {this.renderSense()}
                 </div>
                </Grid>
              </Grid>
        </Grid>
          <div>
            <CustomDialog
              handleDialogOpen={this.handleSettingDialogOpen}
              handleDialogClose={this.handleSettingDialogClose}
              open={this.state.openSettingDialog}
              content={this.state.currentNode}
            />
          </div>
        </div>
    );
  }
}

export default Layout;
