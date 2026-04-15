import 'package:flutter/material.dart';

class LoadingShimmer extends StatefulWidget {
  const LoadingShimmer({super.key});

  @override
  State<LoadingShimmer> createState() => _LoadingShimmerState();
}

class _LoadingShimmerState extends State<LoadingShimmer>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1200),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (BuildContext context, _) {
        final double t = _controller.value;
        final Color c1 = Color.lerp(
          const Color(0xFFD3D0CB),
          const Color(0xFFBEE3DB),
          t,
        )!;
        return Container(
          height: 520,
          decoration: BoxDecoration(
            color: c1,
            borderRadius: BorderRadius.circular(28),
          ),
        );
      },
    );
  }
}
