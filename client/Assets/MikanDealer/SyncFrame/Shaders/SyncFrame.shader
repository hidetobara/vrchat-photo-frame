Shader "MikanDealer/SyncFrame"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _ScaleX("ScaleX", Float) = 1.1
        _ScaleY("ScaleY", Float) = 1.1
        _Color("Color", Color) = (0.5, 0.5, 0.5, 1)
        // 0-1がダウンロード中、1-2が差し替え中
        _Progress("Progress", Float) = 1
        _LoadingType("Loading Type", Int) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 100

        CGINCLUDE

            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float4 _MainTex_ST;
            float _ScaleX;
            float _ScaleY;
            float4 _Color;
            float _Progress;
            int _LoadingType;

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 vertex : SV_POSITION;
                float2 uv : TEXCOORD1;
            };

        ENDCG

        Pass
        {
            Cull Off

            CGPROGRAM

            float3 rand3(float2 st, int seed)
            {
                float3 s = float3(
                    dot(st, float2(127.1, 311.7)) + seed,
                    dot(st, float2(269.5, 183.3)) + seed,
                    dot(st, float2(341.5, 253.1)) + seed);
                return frac(sin(s) * 43758.5453123);
            }

            fixed4 show(float2 uv)
            {
#ifdef UNITY_UV_STARTS_AT_TOP
                float4 col = tex2D(_MainTex, uv);
#else
                float4 col = tex2D(_MainTex, float2(uv.x, 1 - uv.y);
#endif
                if (col.a == 0) discard;
                return fixed4(col);
            }

            fixed4 guruguru(float2 uv)
            {
                float2 lxy = uv - 0.5;
                float ltheta = atan2(lxy.x, lxy.y);
                float ldis = length(lxy);
                float p = pow(sin(-_Time.y * 2 + ltheta) * 0.5 + 0.5, 4);
                if (_Progress < 1)
                {
                    if (0.15 > ldis || ldis > 0.2) discard;
                    if(p < 0.003) discard;
                }

                return lerp(fixed4(_Color.xyz, 1), show(uv), clamp(_Progress - 1, 0, 1));
            }

            fixed4 mosic(float2 uv)
            {
                float3 r = rand3(floor(uv * 30) + floor(_Time.yy) * 17, 123);
                return lerp(fixed4(r, 1), show(uv), clamp(_Progress - 1, 0, 1));
            }

            v2f vert(appdata v)
            {
                v2f o;
                o.vertex = mul(UNITY_MATRIX_VP, mul(UNITY_MATRIX_M, v.vertex * float4(_ScaleX, _ScaleY, 1, 1)));
                o.uv = TRANSFORM_TEX(float2(v.uv.x * _ScaleX - (_ScaleX-1)/2, v.uv.y * _ScaleY - (_ScaleY-1)/2), _MainTex);
                return o;
            }

            fixed4 frag(v2f i, fixed facing : VFACE) : SV_Target
            {
                if (facing < 0)
                {
                    return fixed4(_Color.xyz, 1);
                }

                if (0 <= i.uv.x && i.uv.x <= 1 && 0 <= i.uv.y && i.uv.y <= 1)
                {
                    if (_LoadingType == 1) return mosic(i.uv);
                    return guruguru(i.uv);
                }

                float theta = max(
                    max(-i.uv.x, i.uv.x - 1),
                    max(-i.uv.y, i.uv.y - 1)
                );
                float var = cos(theta * 523) * 0.07 + cos(theta * 701) * 0.05 + cos(theta * 1001 + 0.5) * 0.04;

                return fixed4(_Color.xyz + var.xxx, 1);
            }
            ENDCG
        }
    }
}
