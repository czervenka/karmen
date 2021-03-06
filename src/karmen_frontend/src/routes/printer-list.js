import React from "react";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import Loader from "../components/utils/loader";
import PrinterState from "../components/printers/printer-state";
import { loadAndQueuePrinters } from "../actions/printers";
import formatters from "../services/formatters";

class PrinterList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      timer: null
    };
    this.getPrinters = this.getPrinters.bind(this);
  }

  componentDidMount() {
    this.getPrinters();
  }

  getPrinters() {
    const { printersLoaded, loadPrinters } = this.props;
    let load;
    if (printersLoaded) {
      load = loadPrinters(["status"]);
    } else {
      load = loadPrinters(["job", "status", "webcam"]);
    }
    // We are periodically checking for new printers - this is
    // required for the printers to show up after the network scan
    // or added in a different client.
    // But we are checking only for the local db data, so it should be blazing fast.
    load.then(() => {
      this.setState({
        timer: setTimeout(this.getPrinters, 60 * 1000)
      });
    });
  }

  componentWillUnmount() {
    const { timer } = this.state;
    timer && clearTimeout(timer);
  }

  render() {
    const { printersLoaded, printers } = this.props;
    if (!printersLoaded) {
      return (
        <div>
          <Loader />
        </div>
      );
    }
    const printerElements =
      printers &&
      printers
        .filter(p => !!p)
        .map(printer => {
          return (
            <Link
              className="list-item"
              key={printer.uuid}
              to={`/printers/${printer.uuid}`}
            >
              <div className="list-item-content">
                <span className="list-item-title">{printer.name}</span>
                <span className="list-item-subtitle">
                  <PrinterState printer={printer} />
                </span>

                {printer.job && printer.job.name && (
                  <>
                    <div className="list-item-subtitle">
                      {printer.job.completion && (
                        <span>{printer.job.completion.toFixed(2)}% done, </span>
                      )}
                      <span>
                        ETA: {formatters.timespan(printer.job.printTimeLeft)}
                      </span>
                    </div>
                    <span>{printer.job.name}</span>
                  </>
                )}
              </div>
            </Link>
          );
        });

    return (
      <div className="content printer-list">
        <div className="container">
          <h1 className="main-title">Printers</h1>
        </div>

        <div className="list">{printerElements}</div>
      </div>
    );
  }
}

export default connect(
  state => ({
    printers: state.printers.printers,
    printersLoaded: state.printers.printersLoaded
  }),
  dispatch => ({
    loadPrinters: fields => dispatch(loadAndQueuePrinters(fields))
  })
)(PrinterList);
