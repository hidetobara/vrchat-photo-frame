Shader "MikanDealer/PhotoFrame"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _ScaleX("ScaleX", Float) = 1.1
        _ScaleY("ScaleY", Float) = 1.1
        _CellSize("Cell Size", Float) = 30.0
        _Color("Color", Color) = (0.5, 0.5, 0.5, 1)
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
            float _CellSize;
            float4 _Color;

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 vertex : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

        ENDCG

        Pass
        {
            Cull Back

            CGPROGRAM

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = mul(UNITY_MATRIX_VP, mul(UNITY_MATRIX_M, v.vertex * float4(_ScaleX, _ScaleY, 1, 1)));
                o.uv = TRANSFORM_TEX(float2(v.uv.x * _ScaleX - (_ScaleX-1)/2, v.uv.y * _ScaleY - (_ScaleY-1)/2), _MainTex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                if (0 <= i.uv.x && i.uv.x <= 1 && 0 <= i.uv.y && i.uv.y <= 1)
                {
#ifdef UNITY_UV_STARTS_AT_TOP
                    return tex2D(_MainTex, i.uv);
#else
                    return tex2D(_MainTex, float2(i.uv.x, 1 - i.uv.y);
#endif
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
