import React from "react";

class WebcamStream extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isOnline: true,
      isMaximized: false,
      timer: null,
      snapshotPromise: null
    };
    this.getSnapshot = this.getSnapshot.bind(this);
  }

  getSnapshot() {
    const { url, getWebcamSnapshot } = this.props;
    const { isOnline, snapshotPromise } = this.state;
    if (snapshotPromise || !isOnline) {
      return;
    }
    const newSnapshotPromise = getWebcamSnapshot(url).then(r => {
      if (r.status === 202) {
        this.setState({
          timer: setTimeout(this.getSnapshot, 1000),
          snapshotPromise: null
        });
      } else if (r.data && r.data.prefix && r.data.data) {
        this.setState({
          isOnline: true,
          timer: setTimeout(this.getSnapshot, 1000 / 5), // 1000 / 5 = 5 FPS
          source: `${r.data.prefix}${r.data.data}`,
          snapshotPromise: null
        });
      } else {
        this.setState({
          isOnline: false,
          timer: null,
          source: null,
          snapshotPromise: null
        });
      }
    });
    this.setState({
      snapshotPromise: newSnapshotPromise
    });
  }

  componentDidMount() {
    this.getSnapshot();
  }

  componentWillUnmount() {
    const { timer } = this.state;
    timer && clearTimeout(timer);
    this.setState({
      isOnline: false,
      source: null,
      timer: null
    });
  }

  render() {
    const { url, flipHorizontal, flipVertical, rotate90 } = this.props;
    const { isOnline, isMaximized, source } = this.state;
    let klass = [];
    if (flipHorizontal) {
      klass.push("flip-horizontal");
    }

    if (flipVertical) {
      klass.push("flip-vertical");
    }

    if (rotate90) {
      klass.push("rotate-90");
    }
    return (
      <>
        <div
          className={`webcam-stream ${isOnline && source ? "" : "unavailable"}`}
          onClick={() => {
            if (!isOnline || !source) {
              return;
            }
            this.setState({
              isMaximized: true
            });
          }}
        >
          {isOnline && source ? (
            <img
              className={klass.join(" ")}
              alt={`Current state from ${url}`}
              src={source}
            />
          ) : (
            <div>Stream unavailable</div>
          )}
        </div>
        {isMaximized && (
          <div
            className="webcam-stream maximized"
            onClick={() => {
              this.setState({
                isMaximized: false
              });
            }}
          >
            <div
              className="overlay"
              style={{ backgroundImage: `url(${source})` }}
            ></div>
          </div>
        )}
      </>
    );
  }
}

export default WebcamStream;
