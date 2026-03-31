from argparse import ArgumentParser
from pathlib import Path

from ultralytics import YOLO


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="train_yolov8")
    parser.add_argument("--data", type=str, default="coco128.yaml")
    parser.add_argument("--model", type=str, default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--project", type=str, default=None)
    parser.add_argument("--name", type=str, default="vision_assist_yolov8n")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--cache", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    project_dir = Path(args.project) if args.project else base_dir / "runs" / "train"
    project_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(args.model)

    train_args = {
        "data": args.data,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "workers": args.workers,
        "patience": args.patience,
        "project": str(project_dir),
        "name": args.name,
        "cache": args.cache,
    }
    if args.device:
        train_args["device"] = args.device
    if args.resume:
        train_args["resume"] = args.resume

    model.train(**train_args)
    best = getattr(getattr(model, "trainer", None), "best", None)
    last = getattr(getattr(model, "trainer", None), "last", None)
    print("Training finished.")
    if best:
        print(f"Best checkpoint: {best}")
    if last:
        print(f"Last checkpoint: {last}")


if __name__ == "__main__":
    main()
